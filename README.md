# ✈️ ALX Travel App

A travel booking REST API built with **Django** and **Django REST Framework**: listings, bookings and reviews, **Chapa** payments, and booking confirmation emails sent in the background by **Celery** with **RabbitMQ**. The API is documented with Swagger.

This repository is the final milestone (0x03) of the ALX ProDev Backend travel app project. It holds the complete, runnable project, combining the code from every earlier milestone.

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=flat-square&logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/DRF-A30000?style=flat-square&logo=django&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-37814A?style=flat-square&logo=celery&logoColor=white)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-FF6600?style=flat-square&logo=rabbitmq&logoColor=white)
![Swagger](https://img.shields.io/badge/Swagger-85EA2D?style=flat-square&logo=swagger&logoColor=black)

## Features

- **Listings**: hosts publish properties. Anyone can browse and search them (`?search=nairobi`, `?ordering=price_per_night`). Each listing shows its average rating.
- **Bookings**: signed-in guests book a listing for a date range. The API computes the total price, rejects overlapping stays, and shows users only their own bookings (staff see all of them).
- **Reviews**: one 1–5 star review per guest per listing.
- **Payments**: a [Chapa](https://chapa.co) checkout is started for a booking and then verified. A successful payment marks the booking `confirmed`.
- **Background email**: creating a booking queues `send_booking_confirmation_email` on Celery, so the API responds without waiting for SMTP.
- **Swagger** at `/swagger/`, ReDoc at `/redoc/`, and the raw schema at `/swagger.json`.
- **Seed command** that fills the database with sample users, listings, bookings and reviews.

## Project layout

```
alx_travel_app_0x03/
├── requirements.txt
└── alx_travel_app/                 # Django project root (run commands from here)
    ├── manage.py
    ├── .env.example
    ├── alx_travel_app/             # settings, urls, celery app, wsgi/asgi
    └── listings/
        ├── models.py               # Listing, Booking, Review, Payment
        ├── serializers.py
        ├── views.py                # ViewSets + Chapa InitiatePaymentView / VerifyPaymentView
        ├── urls.py                 # DefaultRouter, mounted under /api/
        ├── chapa.py                # Chapa API client
        ├── tasks.py                # Celery: send_booking_confirmation_email
        ├── permissions.py
        ├── management/commands/seed.py
        ├── migrations/
        └── tests.py
```

## Quick start

You need Python 3.10 or newer. These steps use SQLite and need no other services.

```bash
git clone https://github.com/Dwaynemaster007/alx_travel_app_0x03.git
```

```bash
cd alx_travel_app_0x03
```

```bash
python -m venv venv && source venv/bin/activate
```

```bash
pip install -r requirements.txt
```

```bash
cd alx_travel_app && cp .env.example .env
```

```bash
python manage.py migrate
```

```bash
python manage.py seed
```

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/swagger/. The seed command creates the users `seed_host`, `seed_guest1`, `seed_guest2` and `seed_guest3`, all with the password `password123`. Use one of them with Swagger's **Authorize** button (HTTP Basic), or log in at `/api-auth/login/`. Run `python manage.py createsuperuser` to use the admin site at `/admin/`.

Pass `--listings N` to the seed command to choose how many listings it creates (the default is 10), and `--clear` to delete existing listings first.

The `.env.example` defaults run Celery tasks inside the web process (`CELERY_TASK_ALWAYS_EAGER=True`) and print emails to the console, so you can see confirmation emails without RabbitMQ or SMTP.

## Configuration

All settings come from environment variables or from `alx_travel_app/.env`. See [`.env.example`](alx_travel_app/.env.example) for the full list.

| Variable | Default | Purpose |
| --- | --- | --- |
| `SECRET_KEY` | insecure development key | Django secret key. **Set this in production.** |
| `DEBUG` | `True` | Django debug mode |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated host names |
| `DATABASE_URL` | SQLite `db.sqlite3` | Database connection URL (see below) |
| `CHAPA_SECRET_KEY` | empty | Chapa secret key. Payment endpoints return 503 while it is empty. |
| `CHAPA_CALLBACK_URL` / `CHAPA_RETURN_URL` | this API's verify endpoint / none | Where Chapa calls back, and where it sends the customer after checkout |
| `CELERY_BROKER_URL` | `amqp://guest:guest@localhost:5672//` | RabbitMQ broker |
| `CELERY_TASK_ALWAYS_EAGER` | `False` | `True` runs tasks in the web process with no broker |
| `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL` | console backend | Email delivery |

Never commit `.env` or real keys. `.env` is already listed in `.gitignore`.

### MySQL or PostgreSQL

Install the driver, then point `DATABASE_URL` at the server:

```bash
pip install mysqlclient
```

```dotenv
DATABASE_URL=mysql://alx_user:alx_password@127.0.0.1:3306/alx_travel_app
```

```bash
pip install "psycopg[binary]"
```

```dotenv
DATABASE_URL=postgres://alx_user:alx_password@127.0.0.1:5432/alx_travel_app
```

`mysqlclient` needs the MySQL client headers to build. On Debian or Ubuntu, install them with `apt install default-libmysqlclient-dev pkg-config`. After switching databases, run `python manage.py migrate` again.

## Background emails with Celery and RabbitMQ

1. Start RabbitMQ, for example with Docker:

   ```bash
   docker run -d --name rabbitmq -p 5672:5672 rabbitmq:3
   ```

2. Set `CELERY_TASK_ALWAYS_EAGER=False` in `.env`.
3. From the `alx_travel_app/` directory (next to `manage.py`), start a worker alongside `runserver`:

   ```bash
   celery -A alx_travel_app worker -l info
   ```

Each `POST /api/bookings/` queues `listings.tasks.send_booking_confirmation_email` after the booking is saved, and the worker sends the email. If the broker is down, the booking is still created: the API logs the error and responds after a short timeout rather than hanging.

To send real email, set `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend` and the SMTP variables. With Gmail, use an app password.

## API endpoints

All endpoints are under `/api/`. Write operations need an authenticated user (HTTP Basic or session).

| Method | Endpoint | Description |
| --- | --- | --- |
| GET, POST | `/api/listings/` | List (public) or create listings. The creator becomes the host. |
| GET, PUT, PATCH, DELETE | `/api/listings/{id}/` | Read (public). Only the host can change or delete a listing. |
| GET, POST | `/api/bookings/` | Your bookings, or create one (queues the confirmation email) |
| GET, PUT, PATCH, DELETE | `/api/bookings/{id}/` | Manage one of your bookings |
| GET, POST | `/api/reviews/` | List (public) or create reviews |
| GET, PUT, PATCH, DELETE | `/api/reviews/{id}/` | Read (public). Only the author can change or delete a review. |
| GET | `/api/payments/`, `/api/payments/{id}/` | Your payments |
| POST | `/api/payments/initiate/` | Start a Chapa payment for a booking. Body: `{"booking_id": 1}`. Returns the payment with its `checkout_url`. |
| GET | `/api/payments/verify/{tx_ref}/` | Check the transaction with Chapa and update the payment and booking. Chapa also calls this URL as its callback. |

Example with the seeded data:

```bash
curl -u seed_guest1:password123 -H "Content-Type: application/json" \
  -d '{"listing": 1, "check_in": "2030-06-01", "check_out": "2030-06-04"}' \
  http://127.0.0.1:8000/api/bookings/
```

### Payment flow

1. The guest creates a booking (status `pending`).
2. `POST /api/payments/initiate/` with the booking ID creates a `Payment` with status `Pending` and a unique `tx_ref`, and returns Chapa's `checkout_url`.
3. The guest pays on Chapa's checkout page. Use a `CHASECK_TEST-...` key and Chapa's test cards while developing.
4. Chapa calls `/api/payments/verify/{tx_ref}/`, or you call it yourself. The API asks Chapa for the transaction status. On success the payment becomes `Completed` and the booking `confirmed`. A failed or cancelled transaction marks the payment `Failed`.

If you run locally, Chapa cannot reach `localhost` for the callback. Call the verify endpoint yourself, or expose the server through a tunnel and set `CHAPA_CALLBACK_URL`.

## Tests

```bash
cd alx_travel_app && python manage.py test
```

The tests cover listing, booking and review CRUD and permissions, booking validation, the confirmation email, Chapa initiate and verify (with the Chapa API mocked), the seed command and the Swagger page.

## The travel app series

Each earlier repository holds only the code added in that milestone. This repository combines all of them into one working project.

| Repo | Milestone |
| --- | --- |
| [`alx_travel_app`](https://github.com/Dwaynemaster007/alx_travel_app) | Project setup: Django, DRF, Swagger, MySQL configuration |
| [`alx_travel_app_0x00`](https://github.com/Dwaynemaster007/alx_travel_app_0x00) | Models (`Listing`, `Booking`, `Review`), serializers and a seed command |
| [`alx_travel_app_0x01`](https://github.com/Dwaynemaster007/alx_travel_app_0x01) | CRUD API with DRF `ViewSet`s and routers |
| [`alx_travel_app_0x02`](https://github.com/Dwaynemaster007/alx_travel_app_0x02) | Chapa payment initiation and verification |
| **`alx_travel_app_0x03`** | Celery and RabbitMQ background email tasks, plus the complete app |

## Author

**Thubelihle Dlamini**, [GitHub](https://github.com/Dwaynemaster007) · [LinkedIn](https://linkedin.com/in/thubelihledlamini)
