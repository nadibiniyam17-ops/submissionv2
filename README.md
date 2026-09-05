# Research Submission Portal

Django app for submitting research papers as PDFs and reviewing them from an admin dashboard.

You need **Python 3.12 or newer**.

Install pinned dependencies from `requirements.txt` (Django 6.1, Gunicorn, WhiteNoise, and the Postgres driver). Do not run a bare `pip install django` — a newer Django can break the app.

**Putting it on the internet?** Copy `.env.example` to `.env` and follow **[setup.md](setup.md)**. Do not edit `settings.py` by hand; `git pull` would overwrite those edits. Do not use `runserver` as your public site.

---

## Run it on your computer (PowerShell)

Stay in the **project root** (the folder that contains `README.md` and `submission_portal`). Do not `cd` into `submission_portal` until the steps below say so — `venv` lives in the root, not inside `submission_portal`.

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

cd submission_portal
python manage.py migrate
python manage.py runserver
```

After `Activate.ps1`, the prompt should start with `(venv)`. If it does not, Django is not available and you will get `No module named 'django'`.

If activation fails with an execution-policy error:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then run `.\venv\Scripts\Activate.ps1` again.

You can skip activation and call the venv Python directly (from the project root):

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt
cd submission_portal
..\venv\Scripts\python.exe manage.py migrate
..\venv\Scripts\python.exe manage.py runserver
```

Open **http://127.0.0.1:8000/**

| Page | Local URL |
|------|-----------|
| Submit a paper | http://127.0.0.1:8000/ |
| Check submission status | http://127.0.0.1:8000/status/ |
| Create the first admin | http://127.0.0.1:8000/setup/ |
| Admin login | http://127.0.0.1:8000/login/ |
| Review dashboard | http://127.0.0.1:8000/dashboard/ |

These addresses are for your laptop only. On a real server they become `https://your-domain/...`. See **[setup.md](setup.md)** for every line in the code you must change.

After you submit a paper, the success page shows a **tracking code** (for example `RS-8F3K2P`). Save it. The status link is under the form card on submit and inside the success card after submit. Open `/status/` and enter the code to see whether the paper is pending, under review, or reviewed.

If you close the tab, reopen `/submitted/` or `/status/` in the **same browser** — the code is kept in that browser session. There is no email resend. If the browser data is gone, an admin can still look the code up on the dashboard. The success page is not keyed by a public sequential id.

`/setup/` works only while no admin exists. After that it shows a closed page and you sign in at `/login/`. Only the **first** admin (the account created at `/setup/`) can add more admins from the dashboard. Later admins can review papers but cannot open **Add admin**.

On the submit form, **Type of article** and **Indexed on** include an **Other** choice. Choosing it shows a text field for a custom article type or indexing source.

Stop the laptop server with `Ctrl+C`.

### If it does not start

**`No module named 'django'` / forgot to activate a virtual environment**

You ran `python manage.py runserver` with the system Python instead of the venv. From the **project root**:

```powershell
.\venv\Scripts\Activate.ps1
cd submission_portal
python manage.py runserver
```

If `venv` does not exist yet, create it first with `python -m venv venv` and `pip install -r requirements.txt` (from the project root, venv activated).

**`pip` cannot reach pypi.org / `getaddrinfo failed`**

That is a network or DNS problem, not a Django problem. Fix internet access, then from the project root with the venv activated run `pip install -r requirements.txt`. Do not install Django into system Python.

### Already cloned from GitHub?

```powershell
git clone https://github.com/nadibiniyam17-ops/submissionv2.git
cd submissionv2
```

Use this repository (`submissionv2`). A remote named `origin` that still points at `research-submission-portal` is the wrong target.

Then run the same local commands above.

### macOS / Linux (laptop)

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd submission_portal
python manage.py migrate
python manage.py runserver
```

---

## Host it live (Ubuntu server)

This is a full command set for a typical VPS (Ubuntu 22.04 or 24.04), a domain name, **Nginx**, **Gunicorn**, and **HTTPS**. Replace:

- `YOUR_USER` — Linux username on the server (often `ubuntu`)
- `papers.example.com` — your domain
- `203.0.113.10` — your server’s public IP

`runserver` is only for your laptop. Online you use Gunicorn behind Nginx.

### 0. Domain

In your DNS panel, create an **A record**:

- Host: `@` (and `www` if you want it)
- Value: your server IP

Wait until `ping papers.example.com` reaches that IP.

### 1. SSH into the server

From your computer (PowerShell or Terminal):

```bash
ssh YOUR_USER@203.0.113.10
```

### 2. Install system packages

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip nginx git
```

Python should be 3.12 or newer (`python3 --version`). Ubuntu 24.04 is fine.

### 3. Clone the project

```bash
cd ~
git clone https://github.com/nadibiniyam17-ops/submissionv2.git
cd submissionv2
```

If you already uploaded the files another way, `cd` into the folder that contains `README.md` and `submission_portal`.

### 4. Python environment

```bash
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Gunicorn is the process that runs Django. Nginx is the public front door. Versions are pinned in `requirements.txt`.

### 5. Create `.env` (do not skip)

Follow **[setup.md](setup.md)** now. Copy `.env.example` to `.env` in the project root and set:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG=false`
- `DJANGO_ALLOWED_HOSTS` to your domain
- `DJANGO_CSRF_TRUSTED_ORIGINS` to `https://your-domain`

Leave `PUBLIC_BASE_URL` empty so the status link matches the host visitors actually use.

```bash
cp .env.example .env
nano .env
```

Save and exit (`Ctrl+O`, Enter, `Ctrl+X` in nano).

Generate a secret key (venv still active):

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 6. Database, folders, static files

```bash
cd ~/submissionv2/submission_portal
mkdir -p media
python manage.py migrate
python manage.py collectstatic --noinput
```

`collectstatic` copies CSS and fonts into `staticfiles/` so Nginx can serve them. PDF uploads go in `media/`.

### 7. Test Gunicorn once

Still in `~/submissionv2/submission_portal`, venv active:

```bash
gunicorn submission_portal.wsgi:application --bind 127.0.0.1:8000
```

On your laptop, this should **not** be opened as the public site yet. Leave it running, then in **another** SSH window:

```bash
curl -I http://127.0.0.1:8000/
```

You want HTTP 200. Stop the test with `Ctrl+C` in the Gunicorn window.

### 8. Run Gunicorn as a service

```bash
sudo nano /etc/systemd/system/submission-portal.service
```

Paste this (fix `YOUR_USER` and paths if your home folder is different):

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
    --workers 3 \
    --bind 127.0.0.1:8000 \
    submission_portal.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
```

Then:

```bash
sudo chown -R YOUR_USER:www-data /home/YOUR_USER/submissionv2
sudo chmod -R g+rwx /home/YOUR_USER/submissionv2/submission_portal
sudo systemctl daemon-reload
sudo systemctl enable submission-portal
sudo systemctl start submission-portal
sudo systemctl status submission-portal
```

`status` should say `active (running)`. If it failed:

```bash
sudo journalctl -u submission-portal -n 50 --no-pager
```

### 9. Nginx (public HTTP)

```bash
sudo nano /etc/nginx/sites-available/submission-portal
```

Paste this (replace the domain and `YOUR_USER`):

```nginx
server {
    listen 80;
    server_name papers.example.com;

    client_max_body_size 20M;

    # Both the location and the alias path must end with a slash.
    # If either slash is missing, CSS disappears once DEBUG is false.
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

Do **not** add a public `/media/` location. PDFs are downloaded through the logged-in admin view, not as open files.

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/submission-portal /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Open **http://papers.example.com/** in a browser. CSS should load. Create the first admin at **http://papers.example.com/setup/**.

### 10. Firewall

```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
sudo ufw status
```

### 11. HTTPS (Let’s Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d papers.example.com
```

Follow the prompts (email, agree to terms). Certbot edits Nginx so the site uses `https://`.

Then set `DJANGO_SECURE_SSL=true` in `.env` and restart:

```bash
sudo systemctl restart submission-portal
```

The check-status link is built from the request host, so visitors should see `https://papers.example.com/status/`.

### 12. Confirm everything

| Check | Command or URL |
|--------|----------------|
| App running | `sudo systemctl status submission-portal` |
| Nginx running | `sudo systemctl status nginx` |
| Submit | `https://papers.example.com/` |
| Status | `https://papers.example.com/status/` |
| First admin | `https://papers.example.com/setup/` |
| Login | `https://papers.example.com/login/` |

If you change `.env` later:

```bash
sudo systemctl restart submission-portal
```

If you change CSS or add static files:

```bash
cd ~/submissionv2/submission_portal
source ~/submissionv2/venv/bin/activate
python manage.py collectstatic --noinput
sudo systemctl restart submission-portal
```

### Pulling new code from GitHub later

```bash
cd ~/submissionv2
source venv/bin/activate
git pull
cd submission_portal
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart submission-portal
```

`.env` is gitignored, so `git pull` will not overwrite production secrets. Put Gunicorn’s environment in the systemd unit if you are not loading `.env` from the project root:

```ini
EnvironmentFile=/home/YOUR_USER/submissionv2/.env
```

---

## Other ways to host it

The Ubuntu + Nginx + systemd + Certbot path above is one option. These also work.

### Docker

From the project root, with a filled-in `.env`:

```bash
docker compose up --build
```

The app listens on port 8000. WhiteNoise serves `/static/`. Uploads stay in a volume. Put Nginx or a PaaS load balancer in front for HTTPS.

Postgres instead of SQLite:

```bash
docker compose --profile postgres up --build
```

Set `DATABASE_URL=postgres://portal:portal@db:5432/portal` in `.env`.

### Windows Server

Use **Docker Desktop** and the same `docker compose` command, or run Gunicorn/Waitress on the machine and put IIS or Nginx for Windows in front. Bind the public site to HTTPS. Copy `.env.example` to `.env` the same way. This project does not ship an IIS `web.config`.

### PaaS (Render, Railway, Fly, and similar)

Set the same environment variables as `.env`. Use a Postgres add-on and `DATABASE_URL`. The start command is:

```bash
cd submission_portal && python manage.py migrate && python manage.py collectstatic --noinput && gunicorn submission_portal.wsgi:application --bind 0.0.0.0:$PORT
```

WhiteNoise serves CSS when there is no Nginx.

---

## Postgres, backups, and logs

SQLite on one disk is fine for a laptop and a small class server. Concurrent uploads, moving servers, and backups are weaker on SQLite. For anything shared, use Postgres (`DATABASE_URL`).

**SQLite backup** (stop writes or copy a consistent file):

```bash
sqlite3 submission_portal/db.sqlite3 ".backup /var/backups/portal.sqlite3"
cp -a submission_portal/media /var/backups/portal-media
```

**Postgres backup:**

```bash
pg_dump "$DATABASE_URL" > /var/backups/portal.sql
```

Keep `media/` with the database. A database restore without the PDFs leaves broken downloads.

**Logs:** systemd already sends Gunicorn output to the journal (`journalctl -u submission-portal`). For Nginx, enable logrotate (Ubuntu’s `nginx` package already ships a rotate rule). Example extra file `/etc/logrotate.d/submission-portal` if you add app file logs:

```
/var/log/submission-portal/*.log {
    weekly
    rotate 8
    compress
    missingok
    notifempty
}
```

---

## What you do not get from GitHub

These are local-only (see `.gitignore`):

- `venv/` — recreate with `python -m venv venv` then `pip install -r requirements.txt`
- `.env` and `.secret_key` — local/production secrets; copy from `.env.example`
- `db.sqlite3` — created by `python manage.py migrate` (empty database)
- `media/` — created when someone uploads a PDF
- `staticfiles/` — created on the server by `collectstatic`
- `__pycache__/` and `*.pyc` — created automatically when Python runs

Your submissions and admin accounts stay on the machine that runs the app. Anyone else who clones this repo starts with a fresh database and creates their own admin at `/setup/`.

---

## Contributors

- [nadibiniyam17-ops](https://github.com/nadibiniyam17-ops)
- [aron0707557](https://github.com/aron0707557)
- [yonasgere743](https://github.com/yonasgere743)
