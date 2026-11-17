import os, sqlite3, secrets
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename

BASE = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(BASE, "ares.db")
UPLOAD = os.path.join(BASE, "static", "uploads")
os.makedirs(UPLOAD, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.environ.get("ARES_SECRET_KEY", secrets.token_hex(32))
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024
app.config["UPLOAD_FOLDER"] = UPLOAD
ALLOWED = {"png", "jpg", "jpeg", "gif", "webp"}

def db():
    c = sqlite3.connect(DB)
    c.row_factory = sqlite3.Row
    c.execute("PRAGMA foreign_keys=ON")
    return c

def init_db():
    with db() as c:
        c.executescript("""
        CREATE TABLE IF NOT EXISTS users(
          id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE NOT NULL,
          email TEXT UNIQUE NOT NULL, password TEXT NOT NULL, bio TEXT DEFAULT '',
          avatar TEXT DEFAULT '', is_admin INTEGER DEFAULT 0,
          private INTEGER DEFAULT 0, dark_mode INTEGER DEFAULT 1,
          created TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS posts(
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
          caption TEXT DEFAULT '', image TEXT DEFAULT '', created TEXT NOT NULL,
          FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS likes(
          user_id INTEGER NOT NULL, post_id INTEGER NOT NULL,
          PRIMARY KEY(user_id,post_id),
          FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
          FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS comments(
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
          post_id INTEGER NOT NULL, body TEXT NOT NULL, created TEXT NOT NULL,
          FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
          FOREIGN KEY(post_id) REFERENCES posts(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS stories(
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
          image TEXT NOT NULL, created TEXT NOT NULL,
          FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS messages(
          id INTEGER PRIMARY KEY AUTOINCREMENT, sender_id INTEGER NOT NULL,
          receiver_id INTEGER NOT NULL, body TEXT NOT NULL, created TEXT NOT NULL,
          FOREIGN KEY(sender_id) REFERENCES users(id) ON DELETE CASCADE,
          FOREIGN KEY(receiver_id) REFERENCES users(id) ON DELETE CASCADE);
        CREATE TABLE IF NOT EXISTS notifications(
          id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
          body TEXT NOT NULL, created TEXT NOT NULL, seen INTEGER DEFAULT 0,
          FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE);
        """)
        # The first registered account becomes admin; no default password is created.
init_db()

def current_user():
    if "uid" not in session: return None
    with db() as c:
        return c.execute("SELECT * FROM users WHERE id=?", (session["uid"],)).fetchone()

@app.context_processor
def inject():
    return {"me": current_user(), "year": datetime.now().year}

def login_required(fn):
    @wraps(fn)
    def wrapped(*a, **kw):
        if not current_user():
            flash("Banza winjire muri konti yawe.", "error")
            return redirect(url_for("login"))
        return fn(*a, **kw)
    return wrapped

def save_image(field):
    f = request.files.get(field)
    if not f or not f.filename: return ""
    ext = f.filename.rsplit(".", 1)[-1].lower() if "." in f.filename else ""
    if ext not in ALLOWED:
        raise ValueError("Iyo format y'ifoto ntiyemewe. Koresha PNG, JPG, GIF canke WEBP.")
    name = secrets.token_hex(16) + "." + ext
    f.save(os.path.join(UPLOAD, name))
    return "uploads/" + name

@app.route("/")
def home():
    if not current_user(): return redirect(url_for("login"))
    with db() as c:
        posts = c.execute("""SELECT p.*,u.username,u.avatar,
          (SELECT COUNT(*) FROM likes l WHERE l.post_id=p.id) likes,
          EXISTS(SELECT 1 FROM likes l WHERE l.post_id=p.id AND l.user_id=?) liked
          FROM posts p JOIN users u ON u.id=p.user_id
          ORDER BY p.id DESC""", (session["uid"],)).fetchall()
        stories = c.execute("""SELECT s.*,u.username,u.avatar FROM stories s
          JOIN users u ON u.id=s.user_id WHERE s.created > ?
          ORDER BY s.id DESC""", ((datetime.utcnow()-timedelta(hours=24)).isoformat(),)).fetchall()
        comments = {}
        for p in posts:
            comments[p["id"]] = c.execute("""SELECT c.*,u.username FROM comments c
              JOIN users u ON u.id=c.user_id WHERE post_id=? ORDER BY c.id""", (p["id"],)).fetchall()
    return render_template("home.html", posts=posts, stories=stories, comments=comments)

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method == "POST":
        username=request.form.get("username","").strip()
        email=request.form.get("email","").strip().lower()
        password=request.form.get("password","")
        if len(username)<3 or len(password)<8 or "@" not in email:
            flash("Username igire inyuguti 3+, email ibe nziza, password ibe nibura inyuguti 8.", "error")
            return render_template("register.html")
        try:
            with db() as c:
                count=c.execute("SELECT COUNT(*) FROM users").fetchone()[0]
                if count >= 4:
                    flash("Konti 4 zose zaruzuye. Admin ni we ashobora gucunga abanywanyi.", "error")
                    return render_template("register.html")
                c.execute("INSERT INTO users(username,email,password,is_admin,created) VALUES(?,?,?,?,?)",
                  (username,email,generate_password_hash(password),1 if count==0 else 0,datetime.utcnow().isoformat()))
                uid=c.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()[0]
            session["uid"]=uid
            return redirect(url_for("home"))
        except sqlite3.IntegrityError:
            flash("Username canke email biramaze gukoreshwa.", "error")
    return render_template("register.html")

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        ident=request.form.get("identity","").strip().lower()
        pw=request.form.get("password","")
        with db() as c:
            u=c.execute("SELECT * FROM users WHERE lower(username)=? OR email=?", (ident,ident)).fetchone()
        if u and check_password_hash(u["password"],pw):
            session.clear(); session["uid"]=u["id"]
            return redirect(url_for("home"))
        flash("Username/email canke password si vyo.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/post", methods=["POST"])
@login_required
def create_post():
    caption=request.form.get("caption","").strip()
    try: image=save_image("image")
    except ValueError as e:
        flash(str(e),"error"); return redirect(url_for("home"))
    if not caption and not image:
        flash("Andika ubutumwa canke ushireko ifoto.", "error"); return redirect(url_for("home"))
    with db() as c:
        c.execute("INSERT INTO posts(user_id,caption,image,created) VALUES(?,?,?,?)",
          (session["uid"],caption,image,datetime.utcnow().isoformat()))
    flash("Post yashizwe kuri feed.","success")
    return redirect(url_for("home"))

@app.route("/like/<int:pid>", methods=["POST"])
@login_required
def like(pid):
    with db() as c:
        exists=c.execute("SELECT 1 FROM likes WHERE user_id=? AND post_id=?", (session["uid"],pid)).fetchone()
        if exists: c.execute("DELETE FROM likes WHERE user_id=? AND post_id=?", (session["uid"],pid))
        else:
            c.execute("INSERT OR IGNORE INTO likes(user_id,post_id) VALUES(?,?)",(session["uid"],pid))
            owner=c.execute("SELECT user_id FROM posts WHERE id=?",(pid,)).fetchone()
            if owner and owner["user_id"] != session["uid"]:
                c.execute("INSERT INTO notifications(user_id,body,created) VALUES(?,?,?)",
                  (owner["user_id"],"Umuntu yakunze post yawe.",datetime.utcnow().isoformat()))
    return redirect(request.referrer or url_for("home"))

@app.route("/comment/<int:pid>", methods=["POST"])
@login_required
def comment(pid):
    body=request.form.get("body","").strip()
    if body:
        with db() as c:
            owner=c.execute("SELECT user_id FROM posts WHERE id=?",(pid,)).fetchone()
            if owner:
                c.execute("INSERT INTO comments(user_id,post_id,body,created) VALUES(?,?,?,?)",
                  (session["uid"],pid,body,datetime.utcnow().isoformat()))
                if owner["user_id"] != session["uid"]:
                    c.execute("INSERT INTO notifications(user_id,body,created) VALUES(?,?,?)",
                      (owner["user_id"],"Hari umuntu yagize comment kuri post yawe.",datetime.utcnow().isoformat()))
    return redirect(request.referrer or url_for("home"))

@app.route("/story", methods=["POST"])
@login_required
def story():
    try: image=save_image("image")
    except ValueError as e:
        flash(str(e),"error"); return redirect(url_for("home"))
    if not image:
        flash("Hitamwo ifoto ya story.", "error")
    else:
        with db() as c:
            c.execute("INSERT INTO stories(user_id,image,created) VALUES(?,?,?)",
              (session["uid"],image,datetime.utcnow().isoformat()))
        flash("Story yawe yashizweko.", "success")
    return redirect(url_for("home"))

@app.route("/messages", methods=["GET","POST"])
@login_required
def messages():
    with db() as c:
        people=c.execute("SELECT id,username,avatar FROM users WHERE id!=? ORDER BY username",(session["uid"],)).fetchall()
        target=request.args.get("to", type=int) or (people[0]["id"] if people else None)
        if request.method=="POST":
            target=request.form.get("to",type=int)
            body=request.form.get("body","").strip()
            valid=c.execute("SELECT id FROM users WHERE id=?",(target,)).fetchone()
            if body and valid:
                c.execute("INSERT INTO messages(sender_id,receiver_id,body,created) VALUES(?,?,?,?)",
                  (session["uid"],target,body,datetime.utcnow().isoformat()))
            return redirect(url_for("messages",to=target))
        thread=[]
        if target:
            thread=c.execute("""SELECT m.*,u.username FROM messages m JOIN users u ON u.id=m.sender_id
              WHERE (sender_id=? AND receiver_id=?) OR (sender_id=? AND receiver_id=?)
              ORDER BY m.id""",(session["uid"],target,target,session["uid"])).fetchall()
    return render_template("messages.html",people=people,target=target,thread=thread)

@app.route("/profile/<int:uid>")
@login_required
def profile(uid):
    with db() as c:
        user=c.execute("SELECT * FROM users WHERE id=?",(uid,)).fetchone()
        if not user: return redirect(url_for("home"))
        posts=c.execute("SELECT * FROM posts WHERE user_id=? ORDER BY id DESC",(uid,)).fetchall()
    return render_template("profile.html",user=user,posts=posts)

@app.route("/settings", methods=["GET","POST"])
@login_required
def settings():
    u=current_user()
    if request.method=="POST":
        action=request.form.get("action")
        with db() as c:
            if action=="profile":
                username=request.form.get("username","").strip()
                bio=request.form.get("bio","").strip()[:180]
                avatar=save_image("avatar")
                try:
                    if avatar: c.execute("UPDATE users SET username=?,bio=?,avatar=? WHERE id=?",(username,bio,avatar,u["id"]))
                    else: c.execute("UPDATE users SET username=?,bio=? WHERE id=?",(username,bio,u["id"]))
                    flash("Profile yahinduwe.", "success")
                except sqlite3.IntegrityError: flash("Username irakoreshwa n'uwundi muntu.", "error")
            elif action=="password":
                old=request.form.get("old_password",""); new=request.form.get("new_password","")
                if check_password_hash(u["password"],old) and len(new)>=8:
                    c.execute("UPDATE users SET password=? WHERE id=?",(generate_password_hash(new),u["id"]))
                    flash("Password yahinduwe.", "success")
                else: flash("Password ya kera si yo canke nshasha ni ngufi.", "error")
            elif action=="privacy":
                c.execute("UPDATE users SET private=?,dark_mode=? WHERE id=?",
                  (1 if request.form.get("private") else 0,1 if request.form.get("dark_mode") else 0,u["id"]))
                flash("Preferences zabitswe.", "success")
        return redirect(url_for("settings"))
    users=[]
    if u["is_admin"]:
        with db() as c: users=c.execute("SELECT id,username,email,is_admin,created FROM users ORDER BY id").fetchall()
    return render_template("settings.html",user=u,users=users)

@app.route("/admin/delete/<int:uid>", methods=["POST"])
@login_required
def delete_user(uid):
    if not current_user()["is_admin"] or uid==session["uid"]:
        flash("Ntivyemewe.", "error")
    else:
        with db() as c: c.execute("DELETE FROM users WHERE id=?",(uid,))
        flash("Konti yakuweho.", "success")
    return redirect(url_for("settings"))

@app.route("/notifications")
@login_required
def notifications():
    with db() as c:
        items=c.execute("SELECT * FROM notifications WHERE user_id=? ORDER BY id DESC",(session["uid"],)).fetchall()
        c.execute("UPDATE notifications SET seen=1 WHERE user_id=?",(session["uid"],))
    return render_template("notifications.html",items=items)

@app.route("/manifest.json")
def manifest(): return send_from_directory(BASE,"manifest.json")

@app.route("/sw.js")
def sw(): return send_from_directory(BASE,"sw.js",mimetype="application/javascript")

if __name__ == "__main__":
    app.run(host="0.0.0.0",port=int(os.environ.get("PORT",5000)),debug=False)
