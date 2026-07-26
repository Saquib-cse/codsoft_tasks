# Contact Management System — Backend (Django + DRF)

A secure REST API for users to manage their personal and professional
contacts. Each user only ever sees and modifies their own contacts.

## Stack
- Django 5/6 + Django REST Framework
- Token authentication (`rest_framework.authtoken`)
- SQLite by default (swap `DATABASES` in `settings.py` for Postgres/MySQL in production)
- django-filter for query filtering

## Project structure
```
contact_manager_project/
├── contact_manager/        # project config (settings, root urls)
├── contacts/                # the contacts app
│   ├── models.py            # Contact model + phone validator + duplicate constraints
│   ├── serializers.py       # validation, duplicate-check, registration
│   ├── views.py             # auth + CRUD/list/search views
│   ├── urls.py               # app routes
│   ├── exceptions.py        # consistent error response envelope
│   ├── admin.py              # Django admin registration
│   └── tests.py              # automated test suite (7 tests)
├── manage.py
└── requirements.txt
```

## Setup
```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser   # optional, for /admin/
python manage.py runserver
```

## Auth
All contact endpoints require a token. Register or log in to get one, then
send it as `Authorization: Token <token>` on every request.

### Register
`POST /api/auth/register/`
```json
{"username": "saquib", "email": "s@example.com", "password": "testpass123"}
```
→ `201` `{"username": "saquib", "token": "..."}`

### Login
`POST /api/auth/login/`
```json
{"username": "saquib", "password": "testpass123"}
```
→ `200` `{"username": "saquib", "token": "..."}`

## Contact endpoints

| Method | URL | Description |
|---|---|---|
| GET | `/api/contacts/` | List the current user's contacts (paginated) |
| POST | `/api/contacts/` | Create a contact |
| GET | `/api/contacts/<id>/` | Retrieve one contact |
| PUT/PATCH | `/api/contacts/<id>/` | Update a contact |
| DELETE | `/api/contacts/<id>/` | Delete a contact |

### Query params on the list endpoint
- `?search=<text>` — matches name, email, or phone number
- `?ordering=name` / `?ordering=-created_at` — sort ascending/descending on `name`, `email`, `created_at`, `updated_at`
- `?company=<text>` — exact filter by company
- `?page=<n>` — pagination (10 per page by default, `PAGE_SIZE` in settings.py)

### Contact fields
`name`, `email`, `phone_number`, `address`, `company` (address/company optional).

### Validation & duplicate prevention
- `email` must be a valid email address.
- `phone_number` must be 7–15 digits, optionally prefixed with `+`.
- A user cannot have two contacts with the same email, and cannot have two
  contacts with the same phone number (enforced at both the serializer and
  database level via unique constraints scoped per user).

### Error format
Every error response follows the same shape:
```json
{"error": true, "detail": "A contact with this email or phone number already exists."}
```
Field-specific validation errors additionally include a `fields` object.

## Running tests
```bash
python manage.py test contacts
```
7 tests cover: contact creation, duplicate email rejection, invalid phone
rejection, per-user data isolation, search, update/delete, and blocking
unauthenticated access.
