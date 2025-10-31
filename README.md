# ⚡ Django Background Jobs - Celery + RabbitMQ Integration

A production-ready implementation of asynchronous background task processing using Celery with RabbitMQ as the message broker. Build scalable, non-blocking booking confirmation emails and background jobs for travel applications.

[![Django](https://img.shields.io/badge/Django-4.0+-092E20?style=for-the-badge&logo=django&logoColor=white)](https://www.djangoproject.com/)
[![Celery](https://img.shields.io/badge/Celery-5.0+-37814A?style=for-the-badge&logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3.11+-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white)](https://www.rabbitmq.com/)
[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)

<div align="center">

### 🌟 Async All The Things - Build Scalable Background Tasks 🌟

*Non-blocking operations for better performance and user experience*

[Features](#-key-features) • [Quick Start](#-quick-start) • [Architecture](#-system-architecture) • [Implementation](#-implementation-guide)

</div>

---

## 📋 Project Overview

This project is part of the **ALX ProDev Backend** curriculum (**Milestone 5**), implementing asynchronous background task processing for a travel booking application. Learn to build scalable, non-blocking systems using **Celery** for task management and **RabbitMQ** as the message broker.

### 🎯 Why Async Background Jobs?

**The Problem:**
- ❌ Sending emails blocks HTTP requests
- ❌ Users wait for slow operations to complete
- ❌ Server resources are tied up unnecessarily
- ❌ Poor user experience with delays

**The Solution:**
- ✅ **Instant Response** - Users don't wait for emails
- ✅ **Better Performance** - Free up server resources
- ✅ **Scalability** - Handle thousands of tasks
- ✅ **Reliability** - Retry failed tasks automatically
- ✅ **Monitoring** - Track task status and failures

**Real-World Examples:**
- 📧 **Airbnb** - Booking confirmations
- 🛒 **Amazon** - Order notifications
- ✈️ **Booking.com** - Travel confirmations
- 📱 **Uber** - Receipt emails
- 🎬 **Netflix** - Recommendation processing

---

## 🌟 Key Features

### ⚡ Asynchronous Task Processing
- **Celery Workers** - Distributed task execution
- **RabbitMQ Broker** - Reliable message queuing
- **Background Jobs** - Non-blocking operations
- **Task Scheduling** - Periodic task execution
- **Task Chaining** - Complex workflows

### 📧 Email Notification System
- **Booking Confirmations** - Automated emails
- **SMTP Integration** - Gmail, SendGrid, etc.
- **HTML Templates** - Professional email design
- **Retry Logic** - Handle failures gracefully
- **Rate Limiting** - Prevent spam

### 🔄 Message Queue Features
- **RabbitMQ Broker** - Reliable message delivery
- **Task Routing** - Queue-specific workers
- **Priority Queues** - Important tasks first
- **Dead Letter Queues** - Failed task handling
- **Monitoring** - RabbitMQ Management UI

### 📊 Task Management
- **Task Status** - SUCCESS, PENDING, FAILURE
- **Result Backend** - Store task results
- **Task Revocation** - Cancel running tasks
- **Task ETA** - Schedule future execution
- **Task Expiration** - Auto-cleanup old tasks

---

## 📁 Project Structure

```
alx_travel_app_0x03/
└── alx_travel_app/
    ├── alx_travel_app/           # Project configuration
    │   ├── __init__.py
    │   ├── settings.py           # Django + Celery config
    │   ├── celery.py             # Celery app configuration
    │   ├── urls.py
    │   └── wsgi.py
    ├── listings/                 # Main app
    │   ├── migrations/
    │   ├── __init__.py
    │   ├── models.py             # Booking model
    │   ├── views.py              # BookingViewSet with task trigger
    │   ├── tasks.py              # Celery tasks (email sending)
    │   ├── serializers.py
    │   └── urls.py
    ├── templates/                # Email templates
    │   └── emails/
    │       └── booking_confirmation.html
    ├── manage.py
    ├── requirements.txt          # Dependencies
    └── README.md                 # This file
```

---

## 🚀 Quick Start

### Prerequisites

**Required:**
- **Python 3.9+**
- **Django 4.0+**
- **RabbitMQ** - Message broker
- **SMTP Access** - Gmail or SendGrid
- **Redis** (optional) - For result backend

### System Requirements

**Install RabbitMQ:**

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install rabbitmq-server

# Start RabbitMQ
sudo systemctl start rabbitmq-server
sudo systemctl enable rabbitmq-server

# Enable management plugin
sudo rabbitmq-plugins enable rabbitmq_management
```

**macOS:**
```bash
brew install rabbitmq

# Start RabbitMQ
brew services start rabbitmq
```

**Windows:**
- Download from [RabbitMQ Downloads](https://www.rabbitmq.com/download.html)
- Run installer
- Start RabbitMQ service

### Installation

```bash
# 1️⃣ Clone repository
git clone https://github.com/Dwaynemaster007/alx_travel_app_0x03.git
cd alx_travel_app_0x03/alx_travel_app

# 2️⃣ Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# 3️⃣ Install dependencies
pip install -r requirements.txt

# 4️⃣ Configure environment variables
cp .env.example .env
nano .env  # Edit with your credentials

# 5️⃣ Run migrations
python manage.py makemigrations
python manage.py migrate

# 6️⃣ Create superuser
python manage.py createsuperuser

# 7️⃣ Start Django server
python manage.py runserver

# 8️⃣ Start Celery worker (new terminal)
celery -A alx_travel_app worker --loglevel=info

# 9️⃣ Start Celery beat (optional - for scheduled tasks)
celery -A alx_travel_app beat --loglevel=info
```

### Verify Setup

**Check RabbitMQ:**
```bash
# Check status
sudo systemctl status rabbitmq-server

# Access management UI
# http://localhost:15672
# Default credentials: guest/guest
```

**Check Celery:**
```bash
# List active workers
celery -A alx_travel_app inspect active

# Check registered tasks
celery -A alx_travel_app inspect registered
```

---

## 🏗️ System Architecture

### Architecture Diagram

```
┌─────────────┐
│   Client    │
│  (Browser)  │
└──────┬──────┘
       │ HTTP Request
       ▼
┌─────────────────┐
│  Django Server  │
│  (Web Process)  │
└────────┬────────┘
         │
         │ 1. Save Booking
         │ 2. Trigger Task (delay())
         │
         ▼
┌─────────────────┐
│    RabbitMQ     │
│ (Message Broker)│
└────────┬────────┘
         │
         │ Task Message
         │
         ▼
┌─────────────────┐
│ Celery Worker   │
│ (Background)    │
│                 │
│  📧 Send Email  │
└─────────────────┘
```

### Component Roles

**1. Django Server:**
- Handles HTTP requests
- Creates booking records
- Triggers Celery tasks (non-blocking)
- Returns instant response

**2. RabbitMQ Broker:**
- Receives task messages from Django
- Queues tasks for workers
- Ensures reliable delivery
- Handles task routing

**3. Celery Worker:**
- Consumes tasks from RabbitMQ
- Executes background jobs
- Sends confirmation emails
- Updates task status

**4. Result Backend (Optional):**
- Stores task results
- Tracks task status
- Enables task monitoring

---

## 📖 Implementation Guide

### Step 1: Install Dependencies

**requirements.txt:**
```txt
Django==4.2.0
celery==5.3.0
django-celery-results==2.5.0
amqp==5.1.1
kombu==5.3.0
```

```bash
pip install -r requirements.txt
```

### Step 2: Configure Celery

**File:** `alx_travel_app/celery.py`

```python
import os
from celery import Celery

# Set Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_travel_app.settings')

# Create Celery app
app = Celery('alx_travel_app')

# Load config from Django settings with 'CELERY_' prefix
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks from all installed apps
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery setup"""
    print(f'Request: {self.request!r}')
```

**File:** `alx_travel_app/__init__.py`

```python
# This will make sure the app is always imported when
# Django starts so that shared_task will use this app.
from .celery import app as celery_app

__all__ = ('celery_app',)
```

### Step 3: Configure Django Settings

**File:** `alx_travel_app/settings.py`

```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'django_celery_results',  # Add this
    'listings',
]

# Celery Configuration
CELERY_BROKER_URL = 'amqp://guest:guest@localhost:5672//'
CELERY_RESULT_BACKEND = 'django-db'  # Store results in Django DB
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'UTC'

# Celery Beat Schedule (for periodic tasks)
CELERY_BEAT_SCHEDULE = {
    'send-daily-report': {
        'task': 'listings.tasks.send_daily_report',
        'schedule': 86400.0,  # Every 24 hours
    },
}

# Email Configuration (Gmail Example)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'your-email@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'your-app-password')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# For development: Console email backend
# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
```

**Environment Variables (.env):**
```bash
# Email Configuration
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-gmail-app-password

# RabbitMQ (if custom setup)
CELERY_BROKER_URL=amqp://username:password@localhost:5672//

# Database
DB_NAME=travel_db
DB_USER=postgres
DB_PASSWORD=your-password
```

### Step 4: Create Email Task

**File:** `listings/tasks.py`

```python
from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from .models import Booking
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def send_booking_confirmation_email(self, booking_id):
    """
    Celery task to send booking confirmation email.
    
    Args:
        booking_id: ID of the booking to send confirmation for
    
    Returns:
        str: Success or failure message
    """
    try:
        # Get booking instance
        booking = Booking.objects.get(id=booking_id)
        
        # Prepare email context
        context = {
            'customer_name': booking.customer.get_full_name(),
            'property_name': booking.listing.name,
            'check_in': booking.check_in_date,
            'check_out': booking.check_out_date,
            'total_price': booking.total_price,
            'booking_reference': booking.reference_number,
        }
        
        # Render HTML email template
        html_message = render_to_string(
            'emails/booking_confirmation.html',
            context
        )
        
        # Plain text fallback
        plain_message = f"""
        Booking Confirmation
        
        Dear {context['customer_name']},
        
        Your booking has been confirmed!
        
        Property: {context['property_name']}
        Check-in: {context['check_in']}
        Check-out: {context['check_out']}
        Total: ${context['total_price']}
        Reference: {context['booking_reference']}
        
        Thank you for booking with us!
        """
        
        # Send email
        send_mail(
            subject=f'Booking Confirmation - {context["booking_reference"]}',
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[booking.customer.email],
            html_message=html_message,
            fail_silently=False,
        )
        
        logger.info(f"Confirmation email sent for booking {booking_id}")
        return f"Email sent successfully for booking {booking_id}"
        
    except Booking.DoesNotExist:
        logger.error(f"Booking {booking_id} not found")
        raise
    
    except Exception as exc:
        logger.error(f"Failed to send email for booking {booking_id}: {str(exc)}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))


@shared_task
def send_daily_report():
    """
    Periodic task to send daily booking reports.
    Runs via Celery Beat.
    """
    from django.utils import timezone
    from datetime import timedelta
    
    yesterday = timezone.now() - timedelta(days=1)
    bookings_count = Booking.objects.filter(
        created_at__gte=yesterday
    ).count()
    
    # Send report email to admin
    send_mail(
        subject='Daily Booking Report',
        message=f'Total bookings yesterday: {bookings_count}',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[settings.ADMIN_EMAIL],
        fail_silently=False,
    )
    
    return f"Daily report sent: {bookings_count} bookings"
```

### Step 5: Update Views to Trigger Tasks

**File:** `listings/views.py`

```python
from rest_framework import viewsets, status
from rest_framework.response import Response
from .models import Booking
from .serializers import BookingSerializer
from .tasks import send_booking_confirmation_email
import logging

logger = logging.getLogger(__name__)

class BookingViewSet(viewsets.ModelViewSet):
    """
    ViewSet for booking operations.
    Triggers async email task on booking creation.
    """
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer
    
    def create(self, request, *args, **kwargs):
        """
        Create a new booking and trigger confirmation email task.
        """
        # Validate and save booking
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        booking = serializer.save()
        
        # Trigger async email task (non-blocking)
        send_booking_confirmation_email.delay(booking.id)
        
        logger.info(f"Booking {booking.id} created, email task queued")
        
        # Return instant response (don't wait for email)
        return Response(
            {
                'message': 'Booking created successfully',
                'booking_id': booking.id,
                'email_status': 'queued'
            },
            status=status.HTTP_201_CREATED
        )
    
    def perform_update(self, serializer):
        """
        Update booking and optionally send update notification.
        """
        booking = serializer.save()
        
        # Optionally trigger update notification
        # send_booking_update_email.delay(booking.id)
        
        return booking
```

### Step 6: Create Email Template

**File:** `templates/emails/booking_confirmation.html`

```html
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Booking Confirmation</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f9f9f9;
        }
        .header {
            background-color: #007bff;
            color: white;
            padding: 20px;
            text-align: center;
        }
        .content {
            background-color: white;
            padding: 30px;
            margin-top: 20px;
        }
        .booking-details {
            background-color: #f0f0f0;
            padding: 15px;
            margin: 20px 0;
            border-left: 4px solid #007bff;
        }
        .footer {
            text-align: center;
            margin-top: 20px;
            font-size: 12px;
            color: #666;
        }
        .button {
            display: inline-block;
            padding: 10px 20px;
            background-color: #007bff;
            color: white;
            text-decoration: none;
            border-radius: 5px;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Booking Confirmed!</h1>
        </div>
        
        <div class="content">
            <p>Dear {{ customer_name }},</p>
            
            <p>Great news! Your booking has been confirmed.</p>
            
            <div class="booking-details">
                <h3>Booking Details:</h3>
                <p><strong>Property:</strong> {{ property_name }}</p>
                <p><strong>Check-in:</strong> {{ check_in }}</p>
                <p><strong>Check-out:</strong> {{ check_out }}</p>
                <p><strong>Total Price:</strong> ${{ total_price }}</p>
                <p><strong>Reference Number:</strong> {{ booking_reference }}</p>
            </div>
            
            <p>We're excited to host you! If you have any questions, please don't hesitate to contact us.</p>
            
            <a href="https://yourapp.com/bookings/{{ booking_reference }}" class="button">
                View Booking Details
            </a>
        </div>
        
        <div class="footer">
            <p>Thank you for choosing our service!</p>
            <p>&copy; 2025 Travel App. All rights reserved.</p>
        </div>
    </div>
</body>
</html>
```

---

## 🧪 Testing

### Test Celery Connection

```bash
# Start Celery worker with debug output
celery -A alx_travel_app worker --loglevel=debug

# In another terminal, test task
python manage.py shell
```

```python
from listings.tasks import send_booking_confirmation_email

# Create test booking first, then:
result = send_booking_confirmation_email.delay(1)  # Replace 1 with actual booking ID

# Check task status
print(result.status)  # PENDING, SUCCESS, FAILURE

# Get result (blocks until complete)
print(result.get(timeout=10))
```

### Test Email Sending

```bash
# For development, use console backend in settings.py
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Emails will appear in terminal instead of sending
```

### Monitor Tasks

```bash
# View active tasks
celery -A alx_travel_app inspect active

# View reserved tasks
celery -A alx_travel_app inspect reserved

# View registered tasks
celery -A alx_travel_app inspect registered

# View worker stats
celery -A alx_travel_app inspect stats
```

### RabbitMQ Management UI

Access at `http://localhost:15672` (guest/guest)

**Features:**
- View queues and messages
- Monitor worker connections
- Check message rates
- Manage exchanges and bindings

---

## 🎯 Advanced Features

### Task Priorities

```python
@shared_task(priority=10)  # 0-10, higher = more important
def urgent_task():
    pass

@shared_task(priority=5)
def normal_task():
    pass
```

### Task Retries with Exponential Backoff

```python
@shared_task(bind=True, max_retries=5, default_retry_delay=60)
def retry_task(self):
    try:
        # Task logic
        pass
    except Exception as exc:
        # Retry with exponential backoff
        raise self.retry(
            exc=exc,
            countdown=60 * (2 ** self.request.retries)
        )
```

### Task Chaining

```python
from celery import chain

# Execute tasks in sequence
result = chain(
    task1.s(),
    task2.s(),
    task3.s()
).apply_async()
```

### Task Groups

```python
from celery import group

# Execute tasks in parallel
job = group(
    send_email.s(1),
    send_email.s(2),
    send_email.s(3)
)
result = job.apply_async()
```

### Periodic Tasks with Celery Beat

```python
# In settings.py
from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'send-morning-report': {
        'task': 'listings.tasks.send_daily_report',
        'schedule': crontab(hour=8, minute=0),  # Every day at 8 AM
    },
    'cleanup-old-bookings': {
        'task': 'listings.tasks.cleanup_expired_bookings',
        'schedule': crontab(hour=0, minute=0, day_of_week=0),  # Every Sunday at midnight
    },
}
```

---

## 📊 Monitoring & Debugging

### Flower - Real-time Celery Monitoring

```bash
# Install Flower
pip install flower

# Start Flower
celery -A alx_travel_app flower

# Access dashboard
# http://localhost:5555
```

**Flower Features:**
- Real-time task monitoring
- Worker status and stats
- Task history and details
- Task revocation
- Rate limiting control

### Logging

```python
# In tasks.py
import logging

logger = logging.getLogger(__name__)

@shared_task
def my_task():
    logger.info("Task started")
    try:
        # Task logic
        logger.debug("Processing data...")
        result = process_data()
        logger.info(f"Task completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Task failed: {str(e)}")
        raise
```

### Task Status Tracking

```python
from celery.result import AsyncResult

def check_task_status(task_id):
    result = AsyncResult(task_id)
    return {
        'state': result.state,
        'current': result.info.get('current', 0) if result.info else 0,
        'total': result.info.get('total', 1) if result.info else 1,
        'status': str(result.info) if result.info else 'No info'
    }
```

---

## 🔒 Production Best Practices

### Security

```python
# Use secure broker URL
CELERY_BROKER_URL = 'amqps://username:password@broker.example.com:5671//'

# Enable message signing
CELERY_TASK_SERIALIZER = 'json'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_RESULT_SERIALIZER = 'json'

# Set task time limits
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 60  # 1 minute
```

### Performance

```python
# Worker concurrency
# Start with: celery -A proj worker --concurrency=4

# Prefetch multiplier (tasks per worker)
CELERY_WORKER_PREFETCH_MULTIPLIER = 4

# Disable task result storage if not needed
CELERY_TASK_IGNORE_RESULT = True

# Task compression
CELERY_TASK_COMPRESSION = 'gzip'
```

### Reliability

```python
# Task acknowledgment
CELERY_TASK_ACKS_LATE = True

# Reject on worker lost
CELERY_TASK_REJECT_ON_WORKER_LOST = True

# Result expiration
CELERY_RESULT_EXPIRES = 3600  # 1 hour
```

---

## 🐛 Troubleshooting

### Common Issues

**Celery Worker Won't Start:**
```bash
# Check RabbitMQ is running
sudo systemctl status rabbitmq-server

# Check broker URL is correct
celery -A alx_travel_app inspect ping

# Clear any stuck tasks
celery -A alx_travel_app purge
```

**Tasks Not Executing:**
```bash
# Verify task is registered
celery -A alx_travel_app inspect registered

# Check worker logs
celery -A alx_travel_app worker --loglevel=debug

# Verify task routing
celery -A alx_travel_app inspect active_queues
```

**Email Not Sending:**
```python
# Test email configuration
python manage.py shell

from django.core.mail import send_mail
send_mail(
    'Test',
    'Test message',
    'from@example.com',
    ['to@example.com'],
)

# Check email backend setting
# Use console backend for development
```

**RabbitMQ Connection Refused:**
```bash
# Restart RabbitMQ
sudo systemctl restart rabbitmq-server

# Check RabbitMQ logs
sudo journalctl -u rabbitmq-server

# Verify port is open
telnet localhost 5672
```

---

## 📄 License

This project is part of the **ALX ProDev Backend Curriculum - Milestone 5**.

© 2025 ALX Africa. All rights reserved.

---

## 👨‍💻 Author

**Thubelihle Dlamini (Dwaynemaster007)**

---

<div align="center">

### 💜 Built with Async Excellence by [Dwaynemaster007](https://github.com/Dwaynemaster007) 💜

*Making Everything Non-Blocking, One Task at a Time* ⚡✨

[![GitHub](https://img.shields.io/badge/GitHub-Dwaynemaster007-181717?style=for-the-badge&logo=github)](https://github.com/Dwaynemaster007)
[![Celery](https://img.shields.io/badge/Celery-Master-37814A?style=for-the-badge&logo=celery&logoColor=white)](https://docs.celeryq.dev/)
[![RabbitMQ](https://img.shields.io/badge/RabbitMQ-Expert-FF6600?style=for-the-badge&logo=rabbitmq&logoColor=white)](https://www.rabbitmq.com/)

---

**Tags:** `django` · `celery` · `rabbitmq` · `async` · `background-jobs` · `email-notifications` · `message-queue` · `task-processing` · `booking-confirmations` · `alx-backend` · `milestone-5` · `smtp` · `distributed-systems` · `scalability`

</div>