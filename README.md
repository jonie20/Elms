Employee Leave Management System

Overview

The Employee Leave Management System is a web-based application developed using Django that helps organizations manage employee leave requests efficiently. It allows employees to apply for leave, managers to approve or reject requests, and administrators to track leave balances.

Features

🏢 Employee Registration & Authentication

📅 Apply for Leave (Sick, Casual, Emergency, etc.)

✅ Manager Approval or Rejection

📊 Leave Balance Tracking

📜 Leave History & Reports

🔒 Role-Based Access (Admin, Manager, Employee)

Tech Stack

Backend: Django (Python)

Frontend: HTML, CSS, JavaScript

Database: PostgreSQL / MySQL / SQLite

Authentication: Django Authentication System

API: Django REST Framework (Optional for API integration)

Installation & Setup

Clone the repository

git clone https://github.com/jonie20/Elms.git
cd employee-leave-management

Create & Activate Virtual Environment

python -m venv env
source env/bin/activate  # On Windows use `env\Scripts\activate`

Install Dependencies

pip install -r requirements.txt

Apply Migrations

python manage.py migrate

Create Superuser (Admin Access)

python manage.py createsuperuser

Run the Development Server

python manage.py runserver

Open http://127.0.0.1:8000/ in your browser.

Usage

Employees can log in and request leave

Managers can approve/reject leave requests

Admins can manage employees and leave types



License

This project is licensed under the MIT License.

Contact

📧 Email: kipchimoti@gmail.com
📧 Email: johnstonekipkosgei31@gmail.com
🐙 GitHub: https://github.com/jonie20

