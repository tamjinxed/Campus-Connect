from datetime import datetime
from flask_login import UserMixin
from app import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')
    department = db.Column(db.String(100))
    intake = db.Column(db.String(20))
    bio = db.Column(db.Text)
    avatar_url = db.Column(db.String(300))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    events_organized = db.relationship('Event', foreign_keys='Event.organizer_id', backref='organizer', lazy=True)
    registrations = db.relationship('EventRegistration', backref='user', lazy=True)
    taught_classes = db.relationship('Classroom', backref='teacher', lazy=True)
    memberships = db.relationship('ClassroomMember', backref='student', lazy=True)
    messages = db.relationship('Message', backref='sender', lazy=True)
    announcements = db.relationship('Announcement', foreign_keys='Announcement.author_id', backref='author', lazy=True)

    def is_teacher(self):
        return self.role == 'teacher'

    def is_student(self):
        return self.role == 'student'

class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime)
    location = db.Column(db.String(200))
    category = db.Column(db.String(50), default='general')
    status = db.Column(db.String(20), default='pending')
    organizer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    max_participants = db.Column(db.Integer)
    image_url = db.Column(db.String(300))
    tags = db.Column(db.String(300))
    department = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    registrations = db.relationship('EventRegistration', backref='event', lazy=True, cascade='all, delete-orphan')

    def is_full(self):
        if self.max_participants is None:
            return False
        return len(self.registrations) >= self.max_participants

    def registration_count(self):
        return len(self.registrations)

class EventRegistration(db.Model):
    __tablename__ = 'event_registrations'
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('event_id', 'user_id'),)

class Classroom(db.Model):
    __tablename__ = 'classrooms'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    description = db.Column(db.Text)
    department = db.Column(db.String(100))
    section = db.Column(db.String(20))
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    members = db.relationship('ClassroomMember', backref='classroom', lazy=True, cascade='all, delete-orphan')
    materials = db.relationship('Material', backref='classroom', lazy=True, cascade='all, delete-orphan')

    def member_count(self):
        return len(self.members)

class ClassroomMember(db.Model):
    __tablename__ = 'classroom_members'
    id = db.Column(db.Integer, primary_key=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    __table_args__ = (db.UniqueConstraint('classroom_id', 'student_id'),)

class Material(db.Model):
    __tablename__ = 'materials'
    id = db.Column(db.Integer, primary_key=True)
    classroom_id = db.Column(db.Integer, db.ForeignKey('classrooms.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    file_url = db.Column(db.String(300))
    file_name = db.Column(db.String(200))
    material_type = db.Column(db.String(20), default='note')
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploader = db.relationship('User', foreign_keys=[uploaded_by])

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    room_type = db.Column(db.String(20), nullable=False)
    room_id = db.Column(db.Integer)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Announcement(db.Model):
    __tablename__ = 'announcements'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    priority = db.Column(db.String(20), default='normal')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    approved_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    approver = db.relationship('User', foreign_keys=[approved_by])
