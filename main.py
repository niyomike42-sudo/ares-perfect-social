
import customtkinter as ctk
from tkinter import filedialog
from PIL import Image

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

app = ctk.CTk()
app.title("ARES PERFECT SOCIAL")
app.geometry("1200x780")

GREEN = "#16C76A"
DARK = "#101410"

# MAIN LAYOUT
sidebar = ctk.CTkFrame(app, width=220, fg_color="#080D0A",
                       corner_radius=0)
sidebar.pack(side="left", fill="y")
sidebar.pack_propagate(False)

ctk.CTkLabel(
    sidebar, text="ARES PERFECT",
    font=("Arial", 25, "bold"),
    text_color=GREEN
).pack(pady=(35, 5))

ctk.CTkLabel(
    sidebar, text="SOCIAL NETWORK",
    font=("Arial", 12)
).pack(pady=(0, 35))

def nav_button(name):
    ctk.CTkButton(
        sidebar, text=name, height=48,
        anchor="w", fg_color="transparent",
        hover_color="#193D29",
        font=("Arial", 16)
    ).pack(fill="x", padx=12, pady=5)

for item in [
    "🏠  Home",
    "🔍  Search",
    "❤️  Notifications",
    "✉️  Messages",
    "➕  Create Post",
    "👤  Profile",
    "⚙️  Settings"
]:
    nav_button(item)

ctk.CTkLabel(
    sidebar,
    text="🔒 PRIVATE NETWORK\nONLY 4 MEMBERS",
    text_color=GREEN,
    font=("Arial", 14, "bold")
).pack(side="bottom", pady=35)

# MAIN CONTENT
content = ctk.CTkFrame(app, fg_color=DARK)
content.pack(side="left", fill="both", expand=True)

top = ctk.CTkFrame(content, fg_color=DARK)
top.pack(fill="x", padx=25, pady=20)

ctk.CTkLabel(
    top, text="ARES SOCIAL",
    font=("Arial", 25, "bold"),
    text_color=GREEN
).pack(side="left")

ctk.CTkButton(
    top, text="+ CREATE POST",
    fg_color=GREEN, text_color="black",
    command=lambda: create_post()
).pack(side="right")

# STORIES
ctk.CTkLabel(
    content, text="STORIES",
    font=("Arial", 18, "bold")
).pack(anchor="w", padx=30, pady=(10, 5))

stories = ctk.CTkFrame(content, fg_color="#172019")
stories.pack(fill="x", padx=25, pady=10)

members = [
    "YOU", "USER 02", "USER 03", "USER 04"
]

for member in members:
    ctk.CTkButton(
        stories,
        text="🟢\n" + member,
        width=115, height=80,
        fg_color="#203D2A",
        hover_color="#28633D",
        corner_radius=15
    ).pack(side="left", padx=10, pady=12)

# FEED
ctk.CTkLabel(
    content, text="YOUR FEED",
    font=("Arial", 20, "bold"),
    text_color=GREEN
).pack(anchor="w", padx=30, pady=15)

feed = ctk.CTkScrollableFrame(
    content, fg_color=DARK
)
feed.pack(fill="both", expand=True, padx=25)

def add_post(username, caption, image_path=None):
    card = ctk.CTkFrame(
        feed, fg_color="#1A241D",
        corner_radius=15
    )
    card.pack(fill="x", pady=12, padx=5)

    ctk.CTkLabel(
        card, text="🟢  " + username,
        font=("Arial", 17, "bold"),
        text_color=GREEN
    ).pack(anchor="w", padx=18, pady=12)

    ctk.CTkLabel(
        card, text=caption,
        font=("Arial", 15),
        wraplength=500
    ).pack(anchor="w", padx=18, pady=8)

    if image_path:
        try:
            img = Image.open(image_path)
            img.thumbnail((500, 350))
            photo = ctk.CTkImage(
                light_image=img,
                dark_image=img,
                size=img.size
            )
            picture = ctk.CTkLabel(card, image=photo, text="")
            picture.image = photo
            picture.pack(padx=10, pady=10)
        except Exception as error:
            ctk.CTkLabel(
                card, text="Could not load image"
            ).pack()

    actions = ctk.CTkFrame(card, fg_color="transparent")
    actions.pack(fill="x", padx=15, pady=10)

    likes = [0]
    liked = [False]

    def like_post():
        liked[0] = not liked[0]
        likes[0] += 1 if liked[0] else -1
        like_button.configure(
            text=f"❤️  Like ({likes[0]})"
        )

    like_button = ctk.CTkButton(
        actions, text="❤️  Like (0)",
        fg_color="transparent",
        hover_color="#284A32",
        command=like_post
    )
    like_button.pack(side="left")

    comment_entry = ctk.CTkEntry(
        actions, placeholder_text="Write a comment...",
        width=200
    )
    comment_entry.pack(side="left", padx=8)

    def comment():
        message = comment_entry.get().strip()
        if message:
            ctk.CTkLabel(
                card,
                text="💬 You: " + message,
                wraplength=450
            ).pack(anchor="w", padx=20, pady=5)
            comment_entry.delete(0, "end")

    ctk.CTkButton(
        actions, text="Comment",
        width=85, fg_color=GREEN,
        text_color="black",
        command=comment
    ).pack(side="left")

def create_post():
    dialog = ctk.CTkInputDialog(
        text="Write your publication:",
        title="Create Post"
    )
    caption = dialog.get_input()

    if caption and caption.strip():
        image_path = filedialog.askopenfilename(
            title="Choose a photo (optional)",
            filetypes=[
                ("Images", "*.png *.jpg *.jpeg")
            ]
        )
        add_post("YOU", caption, image_path or None)

# SAMPLE PUBLICATION
add_post(
    "ARES PERFECT",
    "Welcome to ARES PERFECT SOCIAL! 🔥\n"
    "Our private social network for four members."
)

app.mainloop()
