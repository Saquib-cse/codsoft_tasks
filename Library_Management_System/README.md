# Library Management System — Backend

Django + Django REST Framework backend for a library management system:
books, authors, members, issuing/returning, search & pagination, and
overdue/late-fee reporting.

## Stack

- Django 6
- Django REST Framework
- django-filter (search/filtering)
- django-cors-headers (so a separate frontend, e.g. React, can call the API)
- SQLite (default, zero-config)

## Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt

python manage.py migrate
python manage.py createsuperuser   # optional, for /admin/
python manage.py runserver
```

API is served at `http://127.0.0.1:8000/api/`
Admin site at `http://127.0.0.1:8000/admin/`

## Data model

- **Author** — `name`, `bio`
- **Book** — `title`, `isbn` (unique), `authors` (M2M), `genre`,
  `published_date`, `total_copies`, `available_copies` (auto-managed)
- **Member** — `name`, `email` (unique), `phone`, `joined_date`, `is_active`
- **IssuedBook** — `book`, `member`, `issue_date`, `due_date` (auto-set,
  14-day loan period), `return_date`

## Endpoints

| Method | URL | Description |
|---|---|---|
| GET/POST | `/api/books/` | List (search/filter/paginate) or create a book |
| GET/PATCH/DELETE | `/api/books/{id}/` | Retrieve, update, delete a book |
| GET/POST | `/api/authors/` | List or create authors |
| GET/POST | `/api/members/` | List (search/filter/paginate) or create a member |
| GET/PATCH/DELETE | `/api/members/{id}/` | Retrieve, update, delete a member |
| GET/POST | `/api/issues/` | List loans, or issue a book to a member |
| POST | `/api/issues/{id}/return_book/` | Mark a loan returned, computes late fee |
| GET | `/api/reports/` | Library-wide summary stats |
| GET | `/api/reports/overdue/` | All currently overdue loans |

### Query parameters

- Books: `?search=`, `?genre=`, `?available=true|false`, `?ordering=`,
  `?page=`, `?page_size=`
- Members: `?search=`, `?is_active=true|false`, `?page=`
- Issues: `?status=active|overdue|returned`, `?book=`, `?member=`

### Example: issue a book

```bash
curl -X POST http://127.0.0.1:8000/api/issues/ \
  -H "Content-Type: application/json" \
  -d '{"book": 1, "member": 1}'
```

Validation rules enforced server-side:
- A member can't have two active loans of the same book at once.
- A book can't be issued if `available_copies` is 0.
- Inactive members can't borrow.

### Example: return a book

```bash
curl -X POST http://127.0.0.1:8000/api/issues/1/return_book/
```

Response includes `overdue_days` and `late_fee` (₹5/day, configurable via
`IssuedBook.LATE_FEE_PER_DAY` in `library/models.py`).

## Project structure

```
backend/
├── config/          # project settings, root URLs
├── library/
│   ├── models.py      # Author, Book, Member, IssuedBook
│   ├── serializers.py # validation logic lives here
│   ├── views.py        # ViewSets, issue/return action, reports
│   ├── urls.py          # DRF router
│   └── admin.py
├── manage.py
└── requirements.txt
```

## Notes

- `available_copies` is managed automatically — it decrements on issue and
  increments (capped at `total_copies`) on return. Don't edit it directly
  in the API; edit `total_copies` instead and the serializer adjusts the
  delta.
- CORS is pre-configured for `http://localhost:5173` (Vite's default) if
  you connect a React frontend.
