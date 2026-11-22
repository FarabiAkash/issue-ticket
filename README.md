# Issue Ticket

Issue Ticket is a Django app for company projects and the staff who solve them. A company files tickets on its projects. Application staff who are assigned to a project update the status. People assigned to the same project can talk in a live chat room.

## Roles

- **Super Admin** creates application admins and application users, and can open every company, project, and ticket.
- **Application Admin** creates companies and company admins, sees every ticket that is not completed, and assigns application staff to projects.
- **Application User** works tickets only on projects they belong to, including status changes.
- **Company Admin** belongs to one company. They create that company's projects and tickets, and they create company users.
- **Company User** belongs to one company. On assigned projects they can view and create tickets, add notes and screenshots, and chat. They cannot create projects or change status.

A person has one role. Company roles must belong to a company. Staff roles do not. Accounts are deactivated instead of deleted.

There is no ticket assignee. Editing a ticket requires membership on that project, unless the person is a Super Admin or Application Admin. Chat is stricter: only project members can join, including staff.

## Setup

From the project folder, with Python 3.12:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Put a long random string in `SECRET_KEY`. Generate one with:

```powershell
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Then create the database and the first Super Admin:

```powershell
python manage.py migrate
python manage.py createsuperuser
```

`createsuperuser` sets the Super Admin role.

## Run

```powershell
python manage.py runserver
```

Daphne serves the site, including project chat websockets, at `http://127.0.0.1:8000/`. Sign in at `/accounts/login/`.

Leave `REDIS_URL` empty for local development. That uses an in-memory channel layer, which is enough for one server process. Set `REDIS_URL` to a Redis address, for example `redis://localhost:6379/0`, when more than one process must share chat messages.

Uploaded screenshots are stored in `media/`.

## Tests

```powershell
python manage.py test
```

## Layout

```text
accounts/         users, roles, login, user management
organizations/    companies, projects, membership
tickets/          tickets, screenshots, notes, status
chat/             project rooms and the websocket consumer
templates/        shared pages, grouped by area
config/           settings, URLs, and ASGI
```

Product pages live under `templates/`. Django admin at `/admin/` is a developer tool, not the product UI.
