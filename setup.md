# Before you deploy: what to change, and where

Read this **before** you put the site on a real server. The live-hosting commands are in [README.md](README.md). This file is only the **code edits**.

Locally the site is `http://127.0.0.1:8000/`. On the internet it must be **your** address, for example `https://papers.example.com`. If you skip these edits, forms can fail, the status link will still say `127.0.0.1`, or Django will refuse your domain.

There is **one file** to edit in the code:

```
submission_portal/submission_portal/settings.py
```

That is: project folder → `submission_portal` → `submission_portal` → `settings.py`.

Templates (`*.html`) do **not** contain `127.0.0.1`. You do not edit those for deploy.

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

## 2. Open `settings.py` and replace these values

Each block shows **what is in the repo now** and **what it should look like** for a site at `https://papers.example.com`. Swap that example for your address.

### A. `SECRET_KEY` (required on a public server)

**Now (unsafe to leave as-is on the internet):**

```python
SECRET_KEY = 'django-insecure-f3rmrt0%=rzgitflfbukr3_9i-!g=z3#^eb=3=1j@h0i=#m4ru'
```

**Change to** a new random string. On the server, with the venv active:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Paste the output:

```python
SECRET_KEY = 'paste-the-generated-key-here'
```

Do not commit this key to GitHub if the repo is public.

### B. `DEBUG` (required)

**Now:**

```python
DEBUG = True
```

**Change to:**

```python
DEBUG = False
```

`True` is only for your laptop. `False` hides error details from visitors.

### C. `ALLOWED_HOSTS` (required)

This is the **domain or IP**, with no `http://`.

**Now:**

```python
ALLOWED_HOSTS = ['127.0.0.1', 'localhost']
```

**Change to** (add `www.` too if you use it):

```python
ALLOWED_HOSTS = ['papers.example.com']
```

If people can open the site by IP as well:

```python
ALLOWED_HOSTS = ['papers.example.com', '203.0.113.10']
```

If this is wrong, the browser shows `DisallowedHost`.

### D. `CSRF_TRUSTED_ORIGINS` (required)

This must include the **scheme** (`https://` or `http://`). It is not the same as `ALLOWED_HOSTS`.

**Now:**

```python
CSRF_TRUSTED_ORIGINS = [
    'http://127.0.0.1:8000',
    'http://localhost:8000',
]
```

**Change to:**

```python
CSRF_TRUSTED_ORIGINS = [
    'https://papers.example.com',
]
```

If you also serve `www`:

```python
CSRF_TRUSTED_ORIGINS = [
    'https://papers.example.com',
    'https://www.papers.example.com',
]
```

If this is wrong, submit / login / status forms fail with a CSRF error.

### E. `PUBLIC_BASE_URL` (required — this is the check-status link)

This is what authors see under the submit form. Locally it is `http://127.0.0.1:8000/status/`. You must change the host to yours.

**Now:**

```python
PUBLIC_BASE_URL = os.environ.get('PUBLIC_BASE_URL', 'http://127.0.0.1:8000').rstrip('/')
```

**Change to** your full site URL, **no** `/status` and **no** trailing slash:

```python
PUBLIC_BASE_URL = 'https://papers.example.com'
```

The site then shows `https://papers.example.com/status/`.

You can instead keep the `os.environ.get(...)` line and set this on the server:

```bash
export PUBLIC_BASE_URL=https://papers.example.com
```

Restart the app after either method.

### F. `STATIC_ROOT` (leave as-is)

This is already set for production:

```python
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

Do not point it at `127.0.0.1`. The README hosting steps run `collectstatic`, which fills this folder. Nginx then serves `/static/`.

### G. After HTTPS works (recommended)

Still in `settings.py`, **below** the `PUBLIC_BASE_URL` line, add:

```python
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

Add these **only after** Certbot has given you a certificate. If you add them too early, the site can redirect in a loop or fail to load.

---

## 3. Finished example

For `https://papers.example.com`, the top of `settings.py` should look like this:

```python
SECRET_KEY = 'your-new-random-key'

DEBUG = False

ALLOWED_HOSTS = ['papers.example.com']

CSRF_TRUSTED_ORIGINS = [
    'https://papers.example.com',
]

PUBLIC_BASE_URL = 'https://papers.example.com'
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
2. Edited `SECRET_KEY`.
3. Set `DEBUG = False`.
4. Set `ALLOWED_HOSTS` to your domain (no `https://`).
5. Set `CSRF_TRUSTED_ORIGINS` to `https://your-domain` (with `https://`).
6. Set `PUBLIC_BASE_URL` to `https://your-domain` (no slash at the end).
7. Follow **Host it live** in [README.md](README.md).
8. After HTTPS works, add the secure cookie / SSL lines in section G.

---

## 5. What you do **not** change for deploy

| Path | Why |
|------|-----|
| `submission_portal/submissions/templates/` | No localhost URLs. Status link comes from `PUBLIC_BASE_URL`. |
| `submission_portal/submissions/views.py` | Builds `/status/` from `PUBLIC_BASE_URL`. |
| `README.md` | Local `http://127.0.0.1:8000/` examples stay for laptop use. |
| `submission_portal/submissions/static/` | CSS and fonts. `collectstatic` copies them; you do not rewrite URLs here. |

---

## 6. Map of every localhost value in this repo

| File | Name | In the repo today | Change before deploy? |
|------|------|-------------------|------------------------|
| `submission_portal/submission_portal/settings.py` | `SECRET_KEY` | A public demo key | **Yes.** Generate a new one. |
| `submission_portal/submission_portal/settings.py` | `DEBUG` | `True` | **Yes.** Set `False`. |
| `submission_portal/submission_portal/settings.py` | `ALLOWED_HOSTS` | `127.0.0.1`, `localhost` | **Yes.** Your domain or IP. |
| `submission_portal/submission_portal/settings.py` | `CSRF_TRUSTED_ORIGINS` | `http://127.0.0.1:8000`, `http://localhost:8000` | **Yes.** `https://your-domain`. |
| `submission_portal/submission_portal/settings.py` | `PUBLIC_BASE_URL` | `http://127.0.0.1:8000` | **Yes.** `https://your-domain`. |
| `README.md` | Local URL table | `http://127.0.0.1:8000/...` | **No.** Laptop instructions only. |

If a form works on your laptop but CSRF-fails online, `CSRF_TRUSTED_ORIGINS` is the first place to look. If the status sentence still shows `127.0.0.1`, `PUBLIC_BASE_URL` was not changed (or the app was not restarted).
