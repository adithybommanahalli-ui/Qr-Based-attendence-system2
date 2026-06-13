# Smart Attendance System

An AI-powered, production-style web application for marking student attendance using **QR Codes**, **Face Recognition**, and **Geolocation** — built with Flask and a futuristic dark-themed frontend.

---

## ✨ Features

- 🔐 **JWT-based Authentication** (Lecturer & Student roles)
- 📱 **QR Code Sessions** — lecturers generate a unique QR per session
- 🧠 **Face Recognition** — 128-D face descriptors via `face-api.js` (browser-side), Euclidean distance matching on the backend
- 📍 **Geolocation Verification** — Haversine distance check against a configurable radius
- 🚫 **Duplicate Prevention** — one attendance record per student per session
- ⏱️ **Live Session View** — real-time attendance feed, countdown timer, urgency mode when time is running low
- 🎨 **Modern Dark UI** — neon indigo/cyan theme, particle background, cursor spotlight, card tilt effects, magnetic buttons
- ♿ **Accessibility** — respects `prefers-reduced-motion`, graceful camera/GPS permission fallbacks

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask, SQLAlchemy |
| Database | PostgreSQL (or SQLite fallback for local dev) |
| Frontend | HTML, CSS, Vanilla JavaScript |
| Face Recognition | [face-api.js](https://github.com/justadudewhohacks/face-api.js) (CDN) + NumPy (backend comparison) |
| QR Codes | `qrcode` (generation) + [html5-qrcode](https://github.com/mebjas/html5-qrcode) (scanning) |
| Auth | PyJWT + Werkzeug password hashing |
| Geolocation | Browser Geolocation API + Haversine formula |

---

## 📂 Project Structure

```
.
├── main.py                  # Flask app entry point (runs on 0.0.0.0:5000)
├── requirements.txt
├── templates/
│   ├── base.html             # Navbar, particles, toast container
│   ├── index.html            # Landing page
│   ├── login.html
│   ├── register.html         # Registration with face capture
│   ├── lecturer_dashboard.html
│   ├── student_dashboard.html
│   ├── session_view.html     # Live QR + attendance feed
│   └── mark_attendance.html  # QR scan → location → face → result
└── static/
    ├── css/style.css
    └── js/
        ├── common.js          # API helpers, toast, particles, UI effects
        ├── face-capture.js
        └── qr-scanner.js
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.11+
- PostgreSQL (optional — falls back to SQLite if `DATABASE_URL` is not set)

### Installation

```bash
pip install -r requirements.txt
```

### Running

```bash
python main.py
```

The app will be available at **http://localhost:5000**.

On first run, the database tables are auto-created and seeded with a demo lecturer account.

---

## 🔑 Demo Credentials

| Role | Email | Password | Section Code |
|---|---|---|---|
| Lecturer | `lecturer@demo.com` | `demo123` | `DEMO01` |

> Students must register with the section code and complete face registration during sign-up.

---

## 📡 API Overview

### Auth
- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

### Sections (Lecturer)
- `POST /api/section/create`
- `GET /api/section/mine`
- `GET /api/section/<id>/students`
- `GET /api/section/lookup/<code>`

### Sessions
- `POST /api/session/start`
- `POST /api/session/end`
- `GET /api/session/<id>`
- `GET /api/session/active/<section_id>`
- `GET /api/session/qr/<id>`

### Attendance (Student)
- `POST /api/attendance/mark`
- `GET /api/attendance/mine`

All responses follow the format:
```json
{ "success": true|false, "data": {...}, "message": "..." }
```

---

## ✅ Attendance Validation Order

1. Session is active and not expired (auto-ends if past `end_time`)
2. Student belongs to the session's section
3. No duplicate attendance for this session
4. Location within allowed radius (Haversine formula)
5. Face descriptor matches registered face (Euclidean distance < 0.6)

---

## 📝 Notes

- Face matching happens entirely with NumPy on the backend — face descriptors are generated client-side via `face-api.js`.
- The frontend gracefully degrades animation/particle effects on low-end devices and respects reduced-motion preferences.
- Lecturers can start a session without a location restriction if geolocation permission is denied.

---

## 📄 License

This project is provided for educational purposes.

Aditya Basavaraj, CSE DEPARTMENT, GM UNIVERSITY, DAVANGERE
