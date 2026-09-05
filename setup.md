# Before you deploy: what to change, and where

Read this **before** you put the site on a real server. The live-hosting commands are in [README.md](README.md). This file is only the **configuration**.

Do **not** edit `settings.py` for deploy. That file reads environment variables. If you edit it by hand, `git pull` can wipe the edits.

Copy [`.env.example`](.env.example) to `.env` in the project root and change the values there. `.env` is gitignored.

Locally the site is `http://127.0.0.1:8000/`. On the internet it must be **your** address, for example `https://papers.example.com`.

---

## 1. Write your public address

Use this everywhere below. No trailing slash.

| | Example | Yours |
|---|---|---|
| Domain only | `papers.example.com` | |
| Full site URL | `https://papers.example.com` | |
| Status page | `https://papers.example.com/status/` | |

If you only have a server IP for now, use the IP in place of the domain (and `http://` until you add HTTPS).

---

## 2. Create `.env`

From the project root:

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Then edit `.env`.

### A. `DJANGO_SECRET_KEY` (required on a public server)

Generate a key (venv active):

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

```env
DJANGO_SECRET_KEY=paste-the-generated-key-here
```

If this is empty, the app writes a random key to a gitignored `.secret_key` file. That is fine on a laptop. On a server, set the environment variable so workers and restarts share one key.

The old demo key is no longer in `settings.py`.

### B. `DJANGO_DEBUG` (required)

```env
DJANGO_DEBUG=false
```

`true` is only for your laptop. `false` hides error details from visitors.

### C. `DJANGO_ALLOWED_HOSTS` (required)

Domain or IP, no `http://`, comma-separated.

```env
DJANGO_ALLOWED_HOSTS=papers.example.com
```

If people can open the site by IP as well:

```env
DJANGO_ALLOWED_HOSTS=papers.example.com,203.0.113.10
```

### D. `DJANGO_CSRF_TRUSTED_ORIGINS` (required)

Must include the scheme.

```env
DJANGO_CSRF_TRUSTED_ORIGINS=https://papers.example.com
```

If you also serve `www`:

```env
DJANGO_CSRF_TRUSTED_ORIGINS=https://papers.example.com,https://www.papers.example.com
```

### E. Status link

Leave `PUBLIC_BASE_URL` empty. The page prints the host the visitor actually opened, so the visible URL and the click cannot disagree.

Set `PUBLIC_BASE_URL` only if you need a canonical public URL behind a proxy.

### F. Static files

`STATIC_ROOT` is already `staticfiles/`. WhiteNoise serves CSS if Nginx is missing or misconfigured. Still run `collectstatic` on the server.

### G. After HTTPS works

```env
DJANGO_SECURE_SSL=true
```

Add this **only after** the certificate works. Too early and the site can redirect in a loop.

### H. Database

SQLite is the default. For Postgres:

```env
DATABASE_URL=postgres://portal:portal@127.0.0.1:5432/portal
```

---

## 3. Finished example

For `https://papers.example.com`, `.env` should look like this:

```env
DJANGO_SECRET_KEY=your-new-random-key
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=papers.example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://papers.example.com
PUBLIC_BASE_URL=
DJANGO_SECURE_SSL=true
```

Then:

| Visitor wants | URL they use |
|---------------|----------------|
| Submit a paper | `https://papers.example.com/` |
| Check status | `https://papers.example.com/status/` |
| First admin | `https://papers.example.com/setup/` |
| Admin login | `https://papers.example.com/login/` |
| Dashboard | `https://papers.example.com/dashboard/` |

---

## 4. Checklist (do this in order)

1. Domain DNS **A record** points at the server IP (or you are using the IP for now).
2. Copied `.env.example` to `.env`.
3. Set `DJANGO_SECRET_KEY`.
4. Set `DJANGO_DEBUG=false`.
5. Set `DJANGO_ALLOWED_HOSTS` to your domain (no `https://`).
6. Set `DJANGO_CSRF_TRUSTED_ORIGINS` to `https://your-domain`.
7. Follow **Host it live** in [README.md](README.md).
8. After HTTPS works, set `DJANGO_SECURE_SSL=true` and restart.

---

## 5. What you do **not** change for deploy

| Path | Why |
|------|-----|
| `submission_portal/submission_portal/settings.py` | Reads `.env`. Do not paste production secrets here. |
| `submission_portal/submissions/templates/` | No localhost URLs. The status link comes from the current request. |
| `README.md` | Local `http://127.0.0.1:8000/` examples stay for laptop use. |
| `submission_portal/submissions/static/` | CSS and fonts. `collectstatic` copies them. |

If a form works on your laptop but CSRF-fails online, `DJANGO_CSRF_TRUSTED_ORIGINS` is the first place to look.
