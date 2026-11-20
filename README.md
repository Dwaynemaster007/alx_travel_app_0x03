# ✈️ ALX Travel App 0x03: Background Jobs

Milestone 0x03 of the **ALX ProDev Backend** travel booking project. It adds **Celery background tasks** (booking confirmation emails, with RabbitMQ as the broker) on top of the earlier milestones' listings, bookings and **Chapa** payment integration.

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=flat-square&logo=django&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-37814A?style=flat-square&logo=celery&logoColor=white)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-FF6600?style=flat-square&logo=rabbitmq&logoColor=white)

## What's in this milestone

Everything from 0x02, plus:

| File | Purpose |
| --- | --- |
| [`alx_travel_app/celery.py`](alx_travel_app/alx_travel_app/celery.py) | The Celery app, configured from Django settings (`CELERY_*`) |
| [`listings/tasks.py`](alx_travel_app/listings/tasks.py) | `send_booking_confirmation_email`: a `@shared_task` that emails the guest |
| [`listings/views.py`](alx_travel_app/listings/views.py) | `BookingViewSet` queues the email with `.delay()` after a booking is created (if the broker is down, the booking still succeeds and the error is logged) |

### Running the worker

```bash
# RabbitMQ, e.g. with Docker
docker run -d -p 5672:5672 rabbitmq:3
celery -A alx_travel_app worker -l info
```

Emails print to the console by default. For real email, set `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`, `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` in `.env`.

## Run it

You need Python 3.10+. MySQL is optional: leave `DB_NAME` empty in `.env` to use SQLite.

```bash
git clone https://github.com/Dwaynemaster007/alx_travel_app_0x03.git
cd alx_travel_app_0x03
cd alx_travel_app
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt   # mysqlclient needs the MySQL client headers; remove it if you only use SQLite
cp .env.example .env
python manage.py migrate
python manage.py seed           # sample data
python manage.py runserver       # http://localhost:8000/swagger/
python manage.py test listings  # run the tests
```

## The travel app series

Each repository holds the project as it was at the end of one milestone:

| Repo | Milestone |
| --- | --- |
| [`alx_travel_app`](https://github.com/Dwaynemaster007/alx_travel_app) | Project setup: Django, DRF, CORS, Swagger, MySQL/SQLite settings |
| [`alx_travel_app_0x00`](https://github.com/Dwaynemaster007/alx_travel_app_0x00) | Models (`Listing`, `Booking`, `Review`), serializers and a `seed` command |
| [`alx_travel_app_0x01`](https://github.com/Dwaynemaster007/alx_travel_app_0x01) | CRUD API with DRF `ViewSet`s and a router |
| [`alx_travel_app_0x02`](https://github.com/Dwaynemaster007/alx_travel_app_0x02) | Chapa payment initiation and verification |
| **`alx_travel_app_0x03`** | Celery + RabbitMQ booking confirmation emails |

## Author

**Thubelihle Dlamini**, [GitHub](https://github.com/Dwaynemaster007) · [LinkedIn](https://linkedin.com/in/thubelihledlamini)
