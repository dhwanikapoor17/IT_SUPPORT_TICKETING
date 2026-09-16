# IT Support Ticketing System

A full-stack IT support ticketing application featuring a FastAPI backend and a Next.js frontend.

## Quick Start (One-Click Run)

- **Option 1 (Double-Click Batch File):**
  Double click [`start.bat`](file:///c:/Users/Comp-110/Desktop/IT-Support-Ticketing/start.bat) to start both the backend and frontend in separate command windows and open the application in your browser.

- **Option 2 (PowerShell):**
  ```powershell
  .\start.ps1
  ```

## Default Login Credentials

| Role | Email | Password | Dashboard Features |
| :--- | :--- | :--- | :--- |
| **Admin (IT Staff)** | `dhwani.kapoor04@gmail.com` | `admin123` | View all tickets, change status, add remarks |
| **Admin (Backup)** | `admin@test.com` | `admin123` | View all tickets, change status, add remarks |
| **User (Employee)** | `dhwani.kapoors@gmail.com` | *(your signup password)* | Raise tickets, view personal ticket status |
| **User (Demo)** | `dhwani@test.com` | `password123` | Raise tickets, view personal ticket status |

---

## Manual Start

### 1. Backend (FastAPI + PostgreSQL)
```powershell
# Optional: install dependencies if setting up a new environment
pip install -r requirements.txt

cd backend
.\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```
- **Backend API URL:** [http://127.0.0.1:8000](http://127.0.0.1:8000)
- **Interactive Swagger Docs:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **Health Check:** [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

### 2. Frontend (Next.js)
```powershell
cd frontend
npm run dev
```
- **Frontend URL:** [http://localhost:3000](http://localhost:3000)

---

## Architecture

- **Frontend**: Next.js 16 (App Router), React 19, Tailwind CSS
- **Backend**: FastAPI (Python 3.12+), SQLAlchemy, Uvicorn
- **Database**: PostgreSQL (`it_support_db`)
- **Authentication**: JWT Bearer Tokens with PBKDF2 password hashing
- **Notifications**: Automated HTML/Text email alerts on ticket creation and status updates

---

## Automatic Email Notifications (Dual: User & Admin)

The system automatically sends email notifications to **both** parties:

1. **When a Ticket is Created:**
   - **User** receives a confirmation email with their Token ID and ticket summary.
   - **Admin(s)** receive an action alert informing them of the newly submitted ticket, requester details, company, floor, and description.

2. **When Ticket Status Changes / Remarks are Added:**
   - **User** receives a status update email showing the previous &rarr; new status, color-coded badges, and support remarks.
   - **Admin(s)** receive a tracking alert showing who updated the ticket, old/new status, and remarks.

Admin recipients are automatically determined from all registered accounts with `role="admin"` in the database (or optionally set via `ADMIN_EMAIL` in `.env`).

### Configuration (`backend/.env`)

Configure your SMTP provider in [`backend/.env`](file:///c:/Users/Comp-110/Desktop/IT-Support-Ticketing/backend/.env):

```env
# Example for Gmail:
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_gmail_app_password
SMTP_FROM_EMAIL=your_email@gmail.com
SMTP_FROM_NAME="IT Support Desk"
SMTP_USE_TLS=True
```

> **Note:** If SMTP credentials are left blank, notifications are automatically logged to [`backend/email_notifications.log`](file:///c:/Users/Comp-110/Desktop/IT-Support-Ticketing/backend/email_notifications.log) so development and testing continue uninterrupted.

