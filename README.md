# Research Submission Portal

Django app for submitting research papers as PDFs and reviewing them from an admin dashboard.

You need **Python 3.12 or newer**.

## Run it (PowerShell)

Stay in the **project root** (the folder that contains `requirements.txt` and `submission_portal`). Do not `cd` into `submission_portal` until the steps below say so — `requirements.txt` and `venv` live in the root, not inside `submission_portal`.

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

| Page | URL |
|------|-----|
| Submit a paper | http://127.0.0.1:8000/ |
| Create the first admin | http://127.0.0.1:8000/setup/ |
| Admin login | http://127.0.0.1:8000/login/ |
| Review dashboard | http://127.0.0.1:8000/dashboard/ |

`/setup/` works only while no admin exists. After that it shows a closed page and you sign in at `/login/`. Only the **first** admin (the account created at `/setup/`) can add more admins from the dashboard. Later admins can review papers but cannot open **Add admin**.

On the submit form, **Type of article** and **Indexed on** include an **Other** choice. Choosing it shows a text field for a custom article type or indexing source.

Stop the server with `Ctrl+C`.

### If it does not start

**`No module named 'django'` / forgot to activate a virtual environment**

You ran `python manage.py runserver` with the system Python instead of the venv. From the **project root**:

```powershell
.\venv\Scripts\Activate.ps1
cd submission_portal
python manage.py runserver
```

If `venv` does not exist yet, create it first with `python -m venv venv` and `pip install -r requirements.txt` (from the project root).

**`Could not open requirements file: requirements.txt`**

You are inside `submission_portal`. Go up one folder:

```powershell
cd ..
pip install -r requirements.txt
```

**`pip` cannot reach pypi.org / `getaddrinfo failed`**

That is a network or DNS problem, not a Django problem. Fix internet access, then install from the project root with the venv activated. Do not `pip install django` into system Python.

### Already cloned from GitHub?

```powershell
git clone https://github.com/nadibiniyam17-ops/submissionv2.git
cd submissionv2
```

Then run the same commands above.

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cd submission_portal
python manage.py migrate
python manage.py runserver
```

## What you do not get from GitHub

These are local-only (see `.gitignore`):

- `venv/` — recreate with `python -m venv venv`
- `db.sqlite3` — created by `python manage.py migrate` (empty database)
- `media/` — created when someone uploads a PDF
- `__pycache__/` and `*.pyc` — created automatically when Python runs

Your submissions and admin accounts stay on your machine. Anyone else who clones this repo starts with a fresh database and creates their own admin at `/setup/`.

## Contributors

- [nadibiniyam17-ops](https://github.com/nadibiniyam17-ops)
- [aron0707557](https://github.com/aron0707557)
- [yonasgere743](https://github.com/yonasgere743)
