# Research Submission Portal

Django app for submitting research papers as PDFs and reviewing them from an admin dashboard.

You need **Python 3.12 or newer**.

This project only needs Django. Install it with `pip install django` (this app was built on **Django 6.1**; if a brand-new Django release breaks the site, run `pip install "Django>=6.1,<6.2"` instead).

**Putting it on the internet?** First edit `settings.py` using **[setup.md](setup.md)**, then follow **Host it live** below. Do not use `runserver` as your public site.

---

## Run it on your computer (PowerShell)

Stay in the **project root** (the folder that contains `README.md` and `submission_portal`). Do not `cd` into `submission_portal` until the steps below say so — `venv` lives in the root, not inside `submission_portal`.

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install django

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
.\venv\Scripts\python.exe -m pip install django
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

After you submit a paper, the success page shows a **tracking code** (for example `RS-8F3K2P`). Save it. Under the submit form there is a link to `/status/`. Open that page and enter the code to see whether the paper is pending, under review, or reviewed. If someone loses their code, an admin can look it up on the dashboard.

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

If `venv` does not exist yet, create it first with `python -m venv venv` and `pip install django` (from the project root, venv activated).

**`pip` cannot reach pypi.org / `getaddrinfo failed`**

That is a network or DNS problem, not a Django problem. Fix internet access, then from the project root with the venv activated run `pip install django`. Do not install Django into system Python.

### Already cloned from GitHub?

```powershell
git clone https://github.com/nadibiniyam17-ops/submissionv2.git
cd submissionv2
```

Then run the same local commands above.

### macOS / Linux (laptop)

```bash
python3 -m venv venv
source venv/bin/activate
pip install django
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
pip install django gunicorn
```

Gunicorn is the process that runs Django. Nginx is the public front door.

### 5. Edit settings (do not skip)

Follow **[setup.md](setup.md)** now. In `submission_portal/submission_portal/settings.py` you must set:

- a new `SECRET_KEY`
- `DEBUG = False`
- `ALLOWED_HOSTS` to your domain
- `CSRF_TRUSTED_ORIGINS` to `https://your-domain`
- `PUBLIC_BASE_URL` to `https://your-domain`

Until that file is saved, do not continue. The status link will still show `127.0.0.1` if `PUBLIC_BASE_URL` is unchanged.

```bash
nano submission_portal/submission_portal/settings.py
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

Then add the extra HTTPS lines from **setup.md section G** to `settings.py`, and restart:

```bash
sudo systemctl restart submission-portal
```

The check-status link must be `https://papers.example.com/status/` (`PUBLIC_BASE_URL`).

### 12. Confirm everything

| Check | Command or URL |
|--------|----------------|
| App running | `sudo systemctl status submission-portal` |
| Nginx running | `sudo systemctl status nginx` |
| Submit | `https://papers.example.com/` |
| Status | `https://papers.example.com/status/` |
| First admin | `https://papers.example.com/setup/` |
| Login | `https://papers.example.com/login/` |

If you change `settings.py` later:

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

If `git pull` overwrites `settings.py`, put your production values back (see [setup.md](setup.md)).

---

## What you do not get from GitHub

These are local-only (see `.gitignore`):

- `venv/` — recreate with `python -m venv venv` then `pip install django`
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
