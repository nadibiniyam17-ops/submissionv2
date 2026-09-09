# What to change for a domain on a server

Commands (venv, pip, migrate, Gunicorn, Nginx) are in **[README.md](README.md)**. This file is only **what must change** when the site is no longer `http://127.0.0.1:8000/`.

You do **not** edit Django Python, templates, or CSS for a domain. The code already reads environment variables. You change **`.env`**, plus the **domain string** in Nginx (and DNS). If you edit `settings.py` by hand, `git pull` can wipe it.

---

## 1. What you do not change in the code

| Path | Why you leave it alone |
|------|------------------------|
| `submission_portal/submission_portal/settings.py` | Already reads `.env`. Do not paste a secret key or domain here. |
| `submission_portal/submissions/templates/` | No hardcoded laptop URLs. |
| `submission_portal/submissions/views.py` | Reads request host and `.env` settings. |
| `submission_portal/submissions/static/` | CSS and fonts. `collectstatic` copies them on the server. |
| `README.md` | Laptop URLs stay as `127.0.0.1` on purpose. |

If a form works on your laptop but CSRF-fails online, the problem is almost always `DJANGO_CSRF_TRUSTED_ORIGINS` in `.env`, not a template.

---

## 2. Write the public address

No trailing slash.

| | Example | Yours |
|---|---|---|
| Domain only | `papers.example.com` | |
| Full site URL | `https://papers.example.com` | |

If you only have a server IP, use that IP in place of the domain, and `http://` until HTTPS works.

---

## 3. What you change: `.env`

From the project root (see README for the `cp` / `Copy-Item` command):

1. Copy `.env.example` to `.env`.
2. Replace the laptop values with the domain values below.
3. Restart Gunicorn after every `.env` edit (`sudo systemctl restart submission-portal`).

The running app reads **`.env`**, not `.env.example`. `.env` is gitignored.

### `DJANGO_SECRET_KEY` — required on a public server

Generate (venv active):

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

```env
DJANGO_SECRET_KEY=paste-the-generated-key-here
```

Every Gunicorn worker must see the **same** key. Do not leave this empty on a server. Do not reuse a key that was ever committed.

Once `.env` is fully written **and** it includes `DJANGO_SECRET_KEY`, delete the leftover `.secret_key` file in the project root (the app created it as a laptop fallback). The key should live in `.env` only.

```powershell
Remove-Item .secret_key -ErrorAction SilentlyContinue
```

```bash
rm -f .secret_key
```

Do not delete `.env.example`. That template stays in the repo.

### `DJANGO_DEBUG` — required

```env
DJANGO_DEBUG=false
```

`true` is only for a laptop. `false` hides error pages from visitors.

### `DJANGO_ALLOWED_HOSTS` — required

Domain or IP only. **No** `http://` or `https://`.

```env
DJANGO_ALLOWED_HOSTS=papers.example.com
```

Domain and IP:

```env
DJANGO_ALLOWED_HOSTS=papers.example.com,203.0.113.10
```

`www` as well:

```env
DJANGO_ALLOWED_HOSTS=papers.example.com,www.papers.example.com
```

Wrong: `https://papers.example.com` in this line. That causes `DisallowedHost`.

### `DJANGO_CSRF_TRUSTED_ORIGINS` — required

Must include the scheme. After HTTPS:

```env
DJANGO_CSRF_TRUSTED_ORIGINS=https://papers.example.com
```

`www` as well:

```env
DJANGO_CSRF_TRUSTED_ORIGINS=https://papers.example.com,https://www.papers.example.com
```

Still on HTTP only (before Certbot):

```env
DJANGO_CSRF_TRUSTED_ORIGINS=http://papers.example.com
```

Wrong: a host with no scheme. Forms will fail CSRF.

### `DJANGO_SECURE_SSL`

Add **only after** HTTPS (Certbot) works:

```env
DJANGO_SECURE_SSL=true
```

Too early and the site can redirect in a loop.

### `DATABASE_URL`

Leave unset for SQLite. To install Postgres and switch the live site, follow **[README.md](README.md) section 6** (not this file). The `.env` line is:

```env
DATABASE_URL=postgres://portal:YOUR_DB_PASSWORD@127.0.0.1:5432/portal
```

---

## 4. What you change outside `.env` (still not Python)

These strings must match the same domain.

| Place | What to change |
|-------|----------------|
| DNS A record | Host `@` (and `www`) → server IP |
| Nginx `server_name` | `papers.example.com` (your domain) |
| Certbot | `sudo certbot --nginx -d papers.example.com` |
| systemd `EnvironmentFile=` | Path to **this** machine’s `.env` |

Do not add a public Nginx `/media/` location. PDFs go through the logged-in admin download view.

---

## 5. Finished `.env` for a domain

For `https://papers.example.com`:

```env
DJANGO_SECRET_KEY=your-new-random-key
DJANGO_DEBUG=false
DJANGO_ALLOWED_HOSTS=papers.example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://papers.example.com
DJANGO_SECURE_SSL=true
```

| Visitor wants | URL |
|---------------|-----|
| Submit | `https://papers.example.com/` |
| First admin | `https://papers.example.com/setup/` |
| Login | `https://papers.example.com/login/` |
| Dashboard | `https://papers.example.com/dashboard/` |

---

## 6. Checklist

1. DNS A record points at the server (or you are using the IP).
2. `.env` exists (copied from `.env.example`).
3. `DJANGO_SECRET_KEY` is a new random key inside `.env`.
4. `.secret_key` is deleted (the extra file is not needed once the key is in `.env`).
5. `DJANGO_DEBUG=false`.
6. `DJANGO_ALLOWED_HOSTS` is the domain **without** `https://`.
7. `DJANGO_CSRF_TRUSTED_ORIGINS` is `https://your-domain`.
8. Nginx `server_name` is the same domain.
9. Commands in **[README.md](README.md)** section 5 are done.
10. After HTTPS works, `DJANGO_SECURE_SSL=true` and restart Gunicorn.

Nothing in `settings.py` or the templates should have been edited for the domain.
