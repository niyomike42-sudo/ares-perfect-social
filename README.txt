ARES PERFECT SOCIAL V1.0
========================

1) Install Python 3.10 or newer.
2) Open Command Prompt in this folder.
3) Run:
   py -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   python app.py
4) Open http://127.0.0.1:5000 in your browser.
5) Create the FIRST account. It becomes the administrator.
6) Other members register until there are four accounts total.

PHONE ON SAME WIFI:
- Find your laptop's local IPv4 address using `ipconfig`.
- On the phone connected to the same Wi-Fi, open http://LAPTOP-IP:5000
- This local address is for testing only. To use it from different locations,
  deploy the project to a hosting provider with HTTPS and persistent storage.

INSTALL AS AN APP:
- On HTTPS hosting, open the site in Chrome/Edge.
- Choose Install app / Add to Home Screen.

IMPORTANT LIMITATIONS:
- This is a starter MVP, not a production-grade social network.
- Stories are shown for 24 hours; old story records are not automatically deleted.
- Direct messages work as a basic stored text thread, not live push chat.
- PWA offline support is limited to cached shell pages.
- For public deployment, add HTTPS, secure environment secret, CSRF protection,
  rate limiting, database backups, moderation and managed persistent file storage.
- The four-account limit is enforced at registration; first account is admin.
- The first admin account must be created by the owner on a trusted device.
