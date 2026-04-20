import os
import json
import uuid
import math
import base64
import io
from datetime import datetime, timedelta, timezone
from functools import wraps

import numpy as np
import qrcode
from PIL import Image
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, request, jsonify, render_template, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import UniqueConstraint

# ─── App Config ───────────────────────────────────────────────────────────────
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'smart-attendance-secret-key-change-in-prod'

db = SQLAlchemy(app)

# ─── Models ───────────────────────────────────────────────────────────────────
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Section(db.Model):
    __tablename__ = 'section'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(6), unique=True, nullable=False)
    lecturer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=True)
    branch = db.Column(db.String(120), nullable=True)
    face_embedding = db.Column(db.Text, nullable=True)

class Session(db.Model):
    __tablename__ = 'session'
    id = db.Column(db.Integer, primary_key=True)
    section_id = db.Column(db.Integer, db.ForeignKey('section.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    status = db.Column(db.String(20), default='active')
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    radius_meters = db.Column(db.Float, default=100)
    qr_token = db.Column(db.String(64), unique=True, nullable=False)

class Attendance(db.Model):
    __tablename__ = 'attendance'
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('session.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    status = db.Column(db.String(20), default='present')
    reason = db.Column(db.Text, nullable=True)
    __table_args__ = (UniqueConstraint('session_id', 'student_id', name='uq_session_student'),)

# ─── Helpers ──────────────────────────────────────────────────────────────────
def haversine(lat1, lon1, lat2, lon2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def generate_qr_base64(token):
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(token)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return 'data:image/png;base64,' + base64.b64encode(buf.read()).decode('utf-8')

def generate_section_code():
    import random, string
    while True:
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
        if not Section.query.filter_by(code=code).first():
            return code

def success_response(data=None, message='OK', status=200):
    return jsonify({'success': True, 'data': data, 'message': message}), status

def error_response(message='Error', status=400):
    return jsonify({'success': False, 'error': message, 'message': message}), status

def auto_end_session(session):
    now = datetime.now(timezone.utc)
    end = session.end_time
    if end.tzinfo is None:
        end = end.replace(tzinfo=timezone.utc)
    if now > end and session.status == 'active':
        session.status = 'ended'
        db.session.commit()

# ─── Auth Decorators ──────────────────────────────────────────────────────────
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        if not auth.startswith('Bearer '):
            return error_response('Missing or invalid token', 401)
        token = auth.split(' ', 1)[1]
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            user = User.query.get(payload['user_id'])
            if not user:
                return error_response('User not found', 401)
            request.current_user = user
        except jwt.ExpiredSignatureError:
            return error_response('Token expired', 401)
        except jwt.InvalidTokenError:
            return error_response('Invalid token', 401)
        return f(*args, **kwargs)
    return decorated

def role_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(request, 'current_user') or request.current_user.role not in roles:
                return error_response('Forbidden', 403)
            return f(*args, **kwargs)
        return decorated
    return decorator

# ─── Template Routes ──────────────────────────────────────────────────────────
@app.route('/favicon.ico')
def favicon():
    return '', 204

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/lecturer')
def lecturer_dashboard():
    return render_template('lecturer_dashboard.html')

@app.route('/student')
def student_dashboard():
    return render_template('student_dashboard.html')

@app.route('/session/<int:session_id>')
def session_view(session_id):
    return render_template('session_view.html', session_id=session_id)

@app.route('/mark')
def mark_attendance():
    return render_template('mark_attendance.html')

# ─── Auth API ─────────────────────────────────────────────────────────────────
@app.route('/api/auth/register', methods=['POST'])
def api_register():
    try:
        data = request.get_json(force=True)
        name = (data.get('name') or '').strip()
        email = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''
        role = data.get('role') or ''

        if not all([name, email, password, role]):
            return error_response('name, email, password and role are required')
        if role not in ('student', 'lecturer'):
            return error_response('role must be student or lecturer')
        if User.query.filter_by(email=email).first():
            return error_response('Email already registered')

        user = User(
            name=name, email=email,
            password_hash=generate_password_hash(password),
            role=role
        )
        db.session.add(user)
        db.session.flush()

        if role == 'student':
            branch = (data.get('branch') or '').strip()
            section_code = (data.get('section_code') or '').strip().upper()
            face_embedding = data.get('face_embedding')

            if not face_embedding:
                db.session.rollback()
                return error_response('face_embedding is required for students')
            if not isinstance(face_embedding, list) or len(face_embedding) != 128:
                db.session.rollback()
                return error_response('face_embedding must be an array of 128 floats')

            section = None
            if section_code:
                section = Section.query.filter_by(code=section_code).first()
                if not section:
                    db.session.rollback()
                    return error_response(f'Section code {section_code} not found')

            student = Student(
                user_id=user.id,
                section_id=section.id if section else None,
                branch=branch,
                face_embedding=json.dumps(face_embedding)
            )
            db.session.add(student)

        db.session.commit()

        token = jwt.encode(
            {'user_id': user.id, 'exp': datetime.now(timezone.utc) + timedelta(hours=24)},
            app.config['SECRET_KEY'], algorithm='HS256'
        )
        return success_response({
            'token': token,
            'user': {'id': user.id, 'name': user.name, 'email': user.email, 'role': user.role}
        }, 'Registered successfully', 201)
    except Exception as e:
        db.session.rollback()
        return error_response(str(e), 500)

@app.route('/api/auth/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json(force=True)
        email = (data.get('email') or '').strip().lower()
        password = data.get('password') or ''
        if not email or not password:
            return error_response('email and password required')
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password_hash, password):
            return error_response('Invalid email or password', 401)
        token = jwt.encode(
            {'user_id': user.id, 'exp': datetime.now(timezone.utc) + timedelta(hours=24)},
            app.config['SECRET_KEY'], algorithm='HS256'
        )
        return success_response({
            'token': token,
            'user': {'id': user.id, 'name': user.name, 'email': user.email, 'role': user.role}
        })
    except Exception as e:
        return error_response(str(e), 500)

@app.route('/api/auth/me')
@token_required
def api_me():
    try:
        u = request.current_user
        extra = {}
        if u.role == 'student':
            s = Student.query.filter_by(user_id=u.id).first()
            if s:
                sec = Section.query.get(s.section_id) if s.section_id else None
                extra = {
                    'branch': s.branch,
                    'section': {'id': sec.id, 'name': sec.name, 'code': sec.code} if sec else None,
                    'student_id': s.id
                }
        return success_response({
            'id': u.id, 'name': u.name, 'email': u.email, 'role': u.role, **extra
        })
    except Exception as e:
        return error_response(str(e), 500)

# ─── Sections API ─────────────────────────────────────────────────────────────
@app.route('/api/section/create', methods=['POST'])
@token_required
@role_required('lecturer')
def api_section_create():
    try:
        data = request.get_json(force=True)
        name = (data.get('name') or '').strip()
        if not name:
            return error_response('Section name required')
        code = generate_section_code()
        section = Section(name=name, code=code, lecturer_id=request.current_user.id)
        db.session.add(section)
        db.session.commit()
        return success_response({'id': section.id, 'name': section.name, 'code': section.code}, 'Section created', 201)
    except Exception as e:
        db.session.rollback()
        return error_response(str(e), 500)

@app.route('/api/section/mine')
@token_required
@role_required('lecturer')
def api_section_mine():
    try:
        sections = Section.query.filter_by(lecturer_id=request.current_user.id).all()
        result = []
        for s in sections:
            count = Student.query.filter_by(section_id=s.id).count()
            result.append({'id': s.id, 'name': s.name, 'code': s.code, 'student_count': count})
        return success_response(result)
    except Exception as e:
        return error_response(str(e), 500)

@app.route('/api/section/<int:section_id>/students')
@token_required
@role_required('lecturer')
def api_section_students(section_id):
    try:
        section = Section.query.get(section_id)
        if not section or section.lecturer_id != request.current_user.id:
            return error_response('Section not found', 404)
        students = Student.query.filter_by(section_id=section_id).all()
        result = []
        for st in students:
            u = User.query.get(st.user_id)
            result.append({'id': st.id, 'name': u.name, 'email': u.email, 'branch': st.branch})
        return success_response(result)
    except Exception as e:
        return error_response(str(e), 500)

# ─── Sessions API ─────────────────────────────────────────────────────────────
@app.route('/api/session/start', methods=['POST'])
@token_required
@role_required('lecturer')
def api_session_start():
    try:
        data = request.get_json(force=True)
        section_id = data.get('section_id')
        duration = int(data.get('duration_minutes', 10))
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        radius = float(data.get('radius_meters', 100))

        if not section_id:
            return error_response('section_id required')
        section = Section.query.get(section_id)
        if not section or section.lecturer_id != request.current_user.id:
            return error_response('Section not found', 404)

        now = datetime.now(timezone.utc)
        end = now + timedelta(minutes=duration)
        token = str(uuid.uuid4())

        session = Session(
            section_id=section_id,
            start_time=now,
            end_time=end,
            status='active',
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius,
            qr_token=token
        )
        db.session.add(session)
        db.session.commit()

        qr_image = generate_qr_base64(token)
        return success_response({
            'session_id': session.id,
            'qr_token': token,
            'qr_image': qr_image,
            'start_time': now.isoformat(),
            'end_time': end.isoformat(),
            'status': 'active'
        }, 'Session started', 201)
    except Exception as e:
        db.session.rollback()
        return error_response(str(e), 500)

@app.route('/api/session/end', methods=['POST'])
@token_required
@role_required('lecturer')
def api_session_end():
    try:
        data = request.get_json(force=True)
        session_id = data.get('session_id')
        if not session_id:
            return error_response('session_id required')
        session = Session.query.get(session_id)
        if not session:
            return error_response('Session not found', 404)
        section = Section.query.get(session.section_id)
        if section.lecturer_id != request.current_user.id:
            return error_response('Forbidden', 403)
        session.status = 'ended'
        db.session.commit()
        return success_response({'session_id': session.id}, 'Session ended')
    except Exception as e:
        db.session.rollback()
        return error_response(str(e), 500)

@app.route('/api/session/<int:session_id>')
@token_required
def api_session_detail(session_id):
    try:
        session = Session.query.get(session_id)
        if not session:
            return error_response('Session not found', 404)
        auto_end_session(session)

        records = Attendance.query.filter_by(session_id=session_id).all()
        attendance_list = []
        for a in records:
            st = Student.query.get(a.student_id)
            u = User.query.get(st.user_id) if st else None
            attendance_list.append({
                'student_name': u.name if u else 'Unknown',
                'student_email': u.email if u else '',
                'timestamp': a.timestamp.isoformat(),
                'status': a.status,
                'reason': a.reason
            })

        sec = Section.query.get(session.section_id)
        end_dt = session.end_time
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)

        return success_response({
            'id': session.id,
            'section_name': sec.name if sec else '',
            'start_time': session.start_time.isoformat(),
            'end_time': end_dt.isoformat(),
            'status': session.status,
            'qr_token': session.qr_token,
            'attendance': attendance_list
        })
    except Exception as e:
        return error_response(str(e), 500)

@app.route('/api/session/active/<int:section_id>')
@token_required
def api_session_active(section_id):
    try:
        session = Session.query.filter_by(section_id=section_id, status='active').first()
        if not session:
            return success_response(None, 'No active session')
        auto_end_session(session)
        if session.status != 'active':
            return success_response(None, 'No active session')
        return success_response({'session_id': session.id})
    except Exception as e:
        return error_response(str(e), 500)

@app.route('/api/session/qr/<int:session_id>')
@token_required
def api_session_qr(session_id):
    try:
        session = Session.query.get(session_id)
        if not session:
            return error_response('Session not found', 404)
        qr_image = generate_qr_base64(session.qr_token)
        return success_response({'qr_image': qr_image, 'qr_token': session.qr_token})
    except Exception as e:
        return error_response(str(e), 500)

# ─── Attendance API ────────────────────────────────────────────────────────────
@app.route('/api/attendance/mark', methods=['POST'])
@token_required
@role_required('student')
def api_attendance_mark():
    try:
        data = request.get_json(force=True)
        qr_token = data.get('qr_token')
        face_embedding = data.get('face_embedding')
        latitude = data.get('latitude')
        longitude = data.get('longitude')

        if not qr_token:
            return error_response('qr_token required')
        if not face_embedding or not isinstance(face_embedding, list) or len(face_embedding) != 128:
            return error_response('Valid 128-D face_embedding required')
        if latitude is None or longitude is None:
            return error_response('latitude and longitude required')

        # 1. Session check
        session = Session.query.filter_by(qr_token=qr_token).first()
        if not session:
            return error_response('Invalid QR code', 404)
        auto_end_session(session)
        if session.status != 'active':
            return error_response('Session has ended')

        now = datetime.now(timezone.utc)
        end_dt = session.end_time
        if end_dt.tzinfo is None:
            end_dt = end_dt.replace(tzinfo=timezone.utc)
        if now > end_dt:
            session.status = 'ended'
            db.session.commit()
            return error_response('Session has expired')

        # 2. Student belongs to section
        student = Student.query.filter_by(user_id=request.current_user.id).first()
        if not student:
            return error_response('Student profile not found', 404)
        if student.section_id != session.section_id:
            return error_response('You are not enrolled in this section')

        # 3. Duplicate check
        existing = Attendance.query.filter_by(session_id=session.id, student_id=student.id).first()
        if existing:
            return error_response('Attendance already marked for this session')

        # 4. Geolocation check
        if session.latitude is not None and session.longitude is not None:
            dist = haversine(session.latitude, session.longitude, float(latitude), float(longitude))
            if dist > session.radius_meters:
                record = Attendance(
                    session_id=session.id, student_id=student.id,
                    status='rejected', reason=f'Out of range: {dist:.0f}m from class (max {session.radius_meters}m)'
                )
                db.session.add(record)
                db.session.commit()
                return error_response(f'You are too far from the class location ({dist:.0f}m away, max {session.radius_meters}m)', 400)

        # 5. Face recognition
        if not student.face_embedding:
            return error_response('No face data registered for your account')
        stored = np.array(json.loads(student.face_embedding))
        submitted = np.array(face_embedding)
        distance = float(np.linalg.norm(stored - submitted))
        if distance >= 0.6:
            record = Attendance(
                session_id=session.id, student_id=student.id,
                status='rejected', reason=f'Face mismatch (distance={distance:.3f})'
            )
            db.session.add(record)
            db.session.commit()
            return error_response(f'Face verification failed. Please ensure your face is clearly visible.', 400)

        # All checks passed
        record = Attendance(
            session_id=session.id, student_id=student.id,
            status='present'
        )
        db.session.add(record)
        db.session.commit()
        return success_response({'status': 'present'}, 'Attendance marked successfully!')

    except Exception as e:
        db.session.rollback()
        return error_response(str(e), 500)

@app.route('/api/attendance/mine')
@token_required
@role_required('student')
def api_attendance_mine():
    try:
        student = Student.query.filter_by(user_id=request.current_user.id).first()
        if not student:
            return success_response([])
        records = Attendance.query.filter_by(student_id=student.id).order_by(Attendance.timestamp.desc()).all()
        result = []
        for a in records:
            session = Session.query.get(a.session_id)
            sec = Section.query.get(session.section_id) if session else None
            result.append({
                'session_id': a.session_id,
                'section_name': sec.name if sec else '',
                'timestamp': a.timestamp.isoformat(),
                'status': a.status,
                'reason': a.reason
            })
        return success_response(result)
    except Exception as e:
        return error_response(str(e), 500)

# ─── Startup & Seed ───────────────────────────────────────────────────────────
def seed_demo_data():
    if User.query.count() == 0:
        lecturer = User(
            name='Demo Lecturer',
            email='lecturer@demo.com',
            password_hash=generate_password_hash('demo123'),
            role='lecturer'
        )
        db.session.add(lecturer)
        db.session.flush()
        section = Section(name='Demo Class', code='DEMO01', lecturer_id=lecturer.id)
        db.session.add(section)
        db.session.commit()
        print('[SEED] Demo lecturer (lecturer@demo.com / demo123) and section DEMO01 created.')

with app.app_context():
    db.create_all()
    seed_demo_data()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
