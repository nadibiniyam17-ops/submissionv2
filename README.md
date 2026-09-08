# Research Submission Portal

Django app for submitting research papers as PDFs and reviewing them from an admin dashboard.

You need **Python 3.12 or newer**.

| You want | Open this |
|----------|-----------|
| Install, run on a laptop, or host on a server | **This file** (`README.md`) |
| What to change for a real domain (and what not to edit in the code) | **[setup.md](setup.md)** |

Do not edit `settings.py` for deploy. It reads `.env`. `git pull` would overwrite hand-edits. Do not use `runserver` as the public site.

---

## What these files are

Stay in the **project root** — the folder that contains `README.md`, `requirements.txt`, and `submission_portal`. Every command below runs there unless a step says `cd submission_portal`.

| File | What you do with it |
|------|---------------------|
| `requirements.txt` | Package list. **Do not run the file.** Install it with `python -m pip install -r requirements.txt`. |
| `.env.example` | Template. Copy it to `.env`. The app never reads `.env.example`. |
| `.env` | You create this. Laptop: optional. Server: required. Commands are in this README. Exact domain values are in **[setup.md](setup.md)**. Gitignored. |
| `.secret_key` | Auto-created on a laptop if `DJANGO_SECRET_KEY` is empty. After `.env` is complete and includes the key, **delete this file**. Gitignored. |
| `setup.md` | Domain / production values only. Not used at runtime. |
| `README.md` | This file. Commands for users and servers. |

---

## 1. Laptop — install packages

Wrong commands fail: `pip install requirements.txt` (missing `-r`), `python requirements.txt`, or running this inside `submission_portal` where the file is not.

**Windows PowerShell** (project root):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

The `-r` means “read this file as a list.” Without it, pip searches the internet for a package named `requirements.txt`.

If `Activate.ps1` is blocked:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
.\venv\Scripts\Activate.ps1
```

Or skip Activate and call the venv directly:

```powershell
python -m venv venv
.\venv\Scripts\python.exe -m pip install -r requirements.txt
```

Do not run a bare `pip install django`. A newer Django can break the app.

**macOS / Linux:**

```bash
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

---

## 2. Laptop — create `.env` (optional)

Laptop defaults in the code already allow `http://127.0.0.1:8000/`. You can skip this section on a laptop.

To use a local `.env` anyway:

```powershell
Copy-Item .env.example .env
```

```bash
cp .env.example .env
```

Leave the example values (`DJANGO_DEBUG=true`, hosts `127.0.0.1,localhost`). For a **public domain**, stop here and fill the keys as **[setup.md](setup.md)** says, then continue with the server commands in section 5.

Once `.env` is fully written and `DJANGO_SECRET_KEY` is set in that file, delete the extra `.secret_key` file if it exists (`Remove-Item .secret_key` on Windows, `rm -f .secret_key` on Linux). Keep `.env.example`.

---

## 3. Laptop — run the site

After install (venv still active):

```powershell
cd submission_portal
python manage.py migrate
python manage.py runserver
```

If you skipped Activate, use `..\venv\Scripts\python.exe` instead of `python`.

The prompt should start with `(venv)`. If it does not, you will get `No module named 'django'`.

Open **http://127.0.0.1:8000/**

| Page | Laptop URL |
|------|------------|
| Submit a paper | http://127.0.0.1:8000/ |
| Check status | http://127.0.0.1:8000/status/ |
| First admin | http://127.0.0.1:8000/setup/ |
| Admin login | http://127.0.0.1:8000/login/ |
| Review dashboard | http://127.0.0.1:8000/dashboard/ |

After you submit a paper, write down the **tracking code** (for example `RS-8F3K2P`). The status URL sits under the form card. Open `/status/` and enter that code. `/submitted/` shows only the latest code from this browser. The status page does not store codes. If the code is lost, an admin can look it up. There is no email resend.

`/setup/` works only while no admin exists. After that, sign in at `/login/`. Only the first admin can open **Add admin**.

On the submit form, **Type of article** and **Indexed on** include **Other**.

Stop the laptop server with `Ctrl+C`.

### If it does not start

**`No module named 'django'`** — you used system Python. From the project root:

```powershell
.\venv\Scripts\Activate.ps1
cd submission_portal
python manage.py runserver
```

**`pip` / `getaddrinfo failed`** — network or DNS. Fix internet, then `python -m pip install -r requirements.txt` from the project root with the venv on. Do not install Django into system Python.

### Clone from GitHub

```powershell
git clone https://github.com/nadibiniyam17-ops/submissionv2.git
cd submissionv2
```

Then start at section 1. Use this repository (`submissionv2`).

---

## 4. How the site is used

| Who | What they do |
|-----|----------------|
| Author | Opens `/`, submits a PDF, writes down the tracking code, later checks `/status/` |
| First admin | Opens `/setup/` once, then `/login/` and `/dashboard/` to review papers |
| Later admins | Created from the dashboard **Add admin** button (first admin only) |

On a live domain the same paths are `https://your-domain/`, `/status/`, `/setup/`, `/login/`, `/dashboard/`. The values that make Django accept that domain are in **[setup.md](setup.md)**. The commands to install Nginx and Gunicorn stay in this file.

---

## 5. Server — Ubuntu, Nginx, Gunicorn, HTTPS

Replace:

- `YOUR_USER` — Linux username (often `ubuntu`)
- `papers.example.com` — your domain
- `203.0.113.10` — public IP

`runserver` is only for a laptop.

### 5.0 Domain DNS

Create an **A record**: host `@` (and `www` if you want it), value = server IP. Wait until `ping papers.example.com` hits that IP.

### 5.1 SSH

```bash
ssh YOUR_USER@203.0.113.10
```

### 5.2 System packages

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx git
python3 --version
```

Need Python 3.12 or newer. Ubuntu 24.04 is fine.

### 5.3 Clone

```bash
cd ~
git clone https://github.com/nadibiniyam17-ops/submissionv2.git
cd submissionv2
```

If the files are already on the disk, `cd` into the folder that contains `README.md` and `submission_portal`.

### 5.4 Python packages

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 5.5 Create `.env`

```bash
cp .env.example .env
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
nano .env
```

Paste the generated key into `DJANGO_SECRET_KEY`. Set the domain keys exactly as **[setup.md](setup.md)** lists (`DEBUG=false`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, leave `PUBLIC_BASE_URL` empty). Save (`Ctrl+O`, Enter, `Ctrl+X`).

Once `.env` is complete and contains the secret key, delete the leftover file:

```bash
rm -f .secret_key
```

Do not delete `.env` or `.env.example`.

### 5.6 Database and static files

```bash
cd ~/submissionv2/submission_portal
mkdir -p media
python manage.py migrate
python manage.py collectstatic --noinput
```

### 5.7 Test Gunicorn once

Still in `~/submissionv2/submission_portal`, venv active:

```bash
gunicorn --config gunicorn.conf.py submission_portal.wsgi:application
```

In another SSH window:

```bash
curl -I http://127.0.0.1:8000/
```

You want HTTP 200. Stop the test with `Ctrl+C`.

### 5.8 systemd service

```bash
sudo nano /etc/systemd/system/submission-portal.service
```

```ini
[Unit]
Description=Research submission portal
After=network.target

[Service]
User=YOUR_USER
Group=www-data
WorkingDirectory=/home/YOUR_USER/submissionv2/submission_portal
Environment="PATH=/home/YOUR_USER/submissionv2/venv/bin"
EnvironmentFile=/home/YOUR_USER/submissionv2/.env
ExecStart=/home/YOUR_USER/submissionv2/venv/bin/gunicorn \
    --config gunicorn.conf.py \
    submission_portal.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo chown -R YOUR_USER:www-data /home/YOUR_USER/submissionv2
sudo chmod -R g+rwx /home/YOUR_USER/submissionv2/submission_portal
sudo systemctl daemon-reload
sudo systemctl enable submission-portal
sudo systemctl start submission-portal
sudo systemctl status submission-portal
```

If it failed: `sudo journalctl -u submission-portal -n 50 --no-pager`

### 5.9 Nginx

```bash
sudo nano /etc/nginx/sites-available/submission-portal
```

Put **your** domain in `server_name` (see **[setup.md](setup.md)**).

```nginx
server {
    listen 80;
    server_name papers.example.com;

    client_max_body_size 20M;

    location /static/ {
        alias /home/YOUR_USER/submissionv2/submission_portal/staticfiles/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Both `/static/` and the `alias` path must end with a slash. Do **not** add a public `/media/` location.

```bash
sudo ln -s /etc/nginx/sites-available/submission-portal /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Open `http://papers.example.com/`. Create the first admin at `/setup/`.

### 5.10 Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

### 5.11 HTTPS

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d papers.example.com
```

Then set `DJANGO_SECURE_SSL=true` in `.env` (**[setup.md](setup.md)**) and:

```bash
sudo systemctl restart submission-portal
```

### 5.12 Confirm

| Check | Command or URL |
|--------|----------------|
| App | `sudo systemctl status submission-portal` |
| Nginx | `sudo systemctl status nginx` |
| Submit | `https://papers.example.com/` |
| Status | `https://papers.example.com/status/` |
| First admin | `https://papers.example.com/setup/` |
| Login | `https://papers.example.com/login/` |

Change `.env` later → `sudo systemctl restart submission-portal`.

Change CSS →

```bash
cd ~/submissionv2/submission_portal
source ~/submissionv2/venv/bin/activate
python manage.py collectstatic --noinput
sudo systemctl restart submission-portal
```

### Pull new code later

```bash
cd ~/submissionv2
source venv/bin/activate
git pull
cd submission_portal
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart submission-portal
```

`.env` is gitignored, so `git pull` does not overwrite it.

---

## Other ways to host it

### Windows Server

Run Gunicorn or Waitress, put IIS or Nginx for Windows in front, use HTTPS. Create `.env` the same way (**[setup.md](setup.md)**). This project does not ship an IIS `web.config`.

### PaaS (Render, Railway, Fly)

Set the same variables as `.env`. Use a Postgres add-on and `DATABASE_URL`. Start command:

```bash
cd submission_portal && python manage.py migrate && python manage.py collectstatic --noinput && gunicorn --config gunicorn.conf.py --bind 0.0.0.0:$PORT submission_portal.wsgi:application
```

WhiteNoise serves CSS when there is no Nginx.

---

## Postgres, backups, and logs

SQLite is fine on a laptop or a small class server. For anything shared, set `DATABASE_URL` to Postgres (**[setup.md](setup.md)**).

**SQLite backup:**

```bash
sqlite3 submission_portal/db.sqlite3 ".backup /var/backups/portal.sqlite3"
cp -a submission_portal/media /var/backups/portal-media
```

**Postgres backup:**

```bash
pg_dump "$DATABASE_URL" > /var/backups/portal.sql
```

Keep `media/` with the database.

**Logs:** `journalctl -u submission-portal`. Ubuntu’s Nginx package already rotates its own logs.

---

## What you do not get from GitHub

| Path | Recreate with |
|------|----------------|
| `venv/` | `python -m venv venv` then `python -m pip install -r requirements.txt` |
| `.env` | Copy `.env.example`; fill it (laptop defaults, or **[setup.md](setup.md)** on a server) |
| `.secret_key` | Leave it; or set `DJANGO_SECRET_KEY` in `.env` |
| `db.sqlite3` | `python manage.py migrate` |
| `media/` | Created on first PDF upload |
| `staticfiles/` | `python manage.py collectstatic --noinput` |

Anyone who clones the repo starts with an empty database and creates their own admin at `/setup/`.

---

## Contributors

- [nadibiniyam17-ops](https://github.com/nadibiniyam17-ops)
- [aron0707557](https://github.com/aron0707557)
- [yonasgere743](https://github.com/yonasgere743)
