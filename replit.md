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
  js/common.js                 API helpers, toast, auth guards, particles, cursor spotlight, card tilt, magnet effect, lazy script loader, device perf detection
  js/face-capture.js           (legacy — face API now inlined per-page with lazy loadScript())
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

## Frontend UX Overhaul (Applied)
- **Dark futuristic theme**: Neon indigo (#6366f1) + cyan (#22d3ee) on deep dark (#07071a)
- **Ambient particles canvas**: floating particles adapt count to device performance tier
- **Cursor spotlight**: subtle radial glow follows the mouse (skipped on low-end devices)
- **Card 3D tilt**: perspective rotation follows cursor proximity on all cards
- **Button magnetic effect**: primary buttons subtly pull toward the cursor
- **Lazy loading**: face-api.js and html5-qrcode are loaded on-demand per page, not globally
- **Device-adaptive effects**: hardware concurrency + device memory detection gates effects
- **Session view**: radar sweep background, LIVE pulse indicator, urgency mode + red timer when <60s remaining, per-row new-attendance pulse animation
- **Mark attendance**: 4-step progress indicator (QR → Location → Face → Result), rich error taxonomy (face mismatch / out of range / session expired / not enrolled), camera/geo recovery cards with step-by-step instructions, duplicate detection state, processing state with rotating messages
- **Register**: lazy-loaded face-api.js, section code inline verify button with lecturer name preview
- **Lecturer dashboard**: section code copy button, inline student list modal, geo-aware session start with fallback to no-restriction mode
- **Student dashboard**: skeleton loaders during fetch, rich empty state with CTA
- **Reduced-motion support**: `@media (prefers-reduced-motion)` disables all transitions/animations

## Attendance Validation Order
1. Session active & not expired
2. Student enrolled in session's section
3. No duplicate attendance
4. Geolocation within radius (Haversine, default 100m)
5. Face match: Euclidean distance < 0.6 threshold (NumPy)
