# ✈️ ALX Travel App: 0x03 Background Jobs

Milestone 0x03 of the **ALX ProDev Backend** travel booking project. It adds **Celery background tasks** (booking confirmation emails, with RabbitMQ as the broker) on top of the earlier milestones' listings, bookings and **Chapa** payment integration.

![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![Django](https://img.shields.io/badge/Django-092E20?style=flat-square&logo=django&logoColor=white)
![Celery](https://img.shields.io/badge/Celery-37814A?style=flat-square&logo=celery&logoColor=white)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-FF6600?style=flat-square&logo=rabbitmq&logoColor=white)

## What's in this milestone

| File | Purpose |
| --- | --- |
| [`listings/tasks.py`](alx_travel_app/listings/tasks.py) | `send_booking_confirmation_email`: a Celery `@shared_task` that emails the customer after a booking |
| [`listings/views.py`](alx_travel_app/listings/views.py) | `initiate_payment`: starts a Chapa transaction and returns its checkout URL |
| [`listings/models.py`](alx_travel_app/listings/models.py) | `Payment` model that tracks the transaction reference and status |
| [`alx_travel_app/settings.py`](alx_travel_app/alx_travel_app/settings.py) | Celery broker (RabbitMQ), email (SMTP) and Chapa settings |

## The travel app series

Each repository holds the code added in one milestone:

| Repo | Milestone |
| --- | --- |
| [`alx_travel_app`](https://github.com/Dwaynemaster007/alx_travel_app) | Project setup: Django, DRF, Swagger, MySQL configuration |
| [`alx_travel_app_0x00`](https://github.com/Dwaynemaster007/alx_travel_app_0x00) | Models (`Listing`, `Booking`, `Review`), serializers and a seed command |
| [`alx_travel_app_0x01`](https://github.com/Dwaynemaster007/alx_travel_app_0x01) | CRUD API with DRF `ViewSet`s and routers |
| [`alx_travel_app_0x02`](https://github.com/Dwaynemaster007/alx_travel_app_0x02) | Chapa payment initiation and verification |
| **`alx_travel_app_0x03`** | Celery + RabbitMQ background email tasks |

## Running the worker

With the full project assembled (see the series above) and RabbitMQ running:

```bash
pip install django djangorestframework celery requests
celery -A alx_travel_app worker -l info
```

Set `CHAPA_SECRET_KEY`, `EMAIL_HOST_USER` and `EMAIL_HOST_PASSWORD` as environment variables. Never commit them.

## Author

**Thubelihle Dlamini**, [GitHub](https://github.com/Dwaynemaster007) · [LinkedIn](https://linkedin.com/in/thubelihledlamini)
