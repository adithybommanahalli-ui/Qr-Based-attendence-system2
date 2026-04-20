# Smart Attendance System

## Overview
A full-stack AI-powered attendance platform using QR Code, Face Recognition (face-api.js), and Geolocation.

## Tech Stack
- **Backend**: Python Flask + SQLAlchemy (SQLite)
- **Frontend**: Plain HTML/CSS/Vanilla JS (served by Flask templates)
- **Face Recognition**: face-api.js (browser-side, CDN) — generates 128-D face descriptors. Python uses NumPy for Euclidean distance comparison.
- **QR Code**: `qrcode` Python library (generation) + `html5-qrcode` CDN (scanning)
- **Auth**: JWT via PyJWT, password hashing via Werkzeug
- **Geolocation**: Browser Geolocation API + Python Haversine formula

## Project Structure
```
main.py                        Flask app (runs on 0.0.0.0:5000)
requirements.txt
database.db                    Auto-created on first run
templates/
  base.html                    Navbar, CDN imports, toast container
  index.html                   Landing page with demo credentials
  login.html                   Login form
  register.html                Registration with face capture
  lecturer_dashboard.html      Sections + Start Session
  student_dashboard.html       Attendance history + stats
  session_view.html            QR display + live attendance list
  mark_attendance.html         QR scan → geo → face → submit
static/
  css/style.css
  js/common.js                 API helpers, toast, auth guards
  js/face-capture.js           face-api.js model loading + detection
  js/qr-scanner.js             QR scanner helpers
```

## Demo Credentials (auto-seeded)
- **Lecturer**: lecturer@demo.com / demo123
- **Section code**: DEMO01

## Running
Workflow: `python main.py` on port 5000

## Key API Routes
- POST /api/auth/register, /api/auth/login, GET /api/auth/me
- POST /api/section/create, GET /api/section/mine, GET /api/section/<id>/students
- POST /api/session/start, POST /api/session/end, GET /api/session/<id>
- POST /api/attendance/mark, GET /api/attendance/mine

## Attendance Validation Order
1. Session active & not expired
2. Student enrolled in session's section
3. No duplicate attendance
4. Geolocation within radius (Haversine, default 100m)
5. Face match: Euclidean distance < 0.6 threshold (NumPy)
