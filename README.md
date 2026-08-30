# Research Submission Portal

Django app for submitting research papers as PDFs and reviewing them from an admin dashboard.

You need **Python 3.12 or newer**.

## Run it (PowerShell)

From the folder that contains `requirements.txt` and `submission_portal`:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

cd submission_portal
python manage.py migrate
python manage.py runserver
```

If activation fails with an execution-policy error:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

Then run `.\venv\Scripts\Activate.ps1` again.

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
