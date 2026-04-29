from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_socketio import emit, join_room, leave_room
from datetime import datetime
from app import db, socketio
from app.models import Message, Classroom, ClassroomMember
from app.chat import chat_bp

@chat_bp.route('/')
@login_required
def index():
    if current_user.is_teacher():
        classrooms = Classroom.query.filter_by(teacher_id=current_user.id).all()
    else:
        memberships = ClassroomMember.query.filter_by(student_id=current_user.id).all()
        classroom_ids = [m.classroom_id for m in memberships]
        classrooms = Classroom.query.filter(Classroom.id.in_(classroom_ids)).all()
    return render_template('chat/index.html', classrooms=classrooms)

@chat_bp.route('/global')
@login_required
def global_chat():
    messages = Message.query.filter_by(room_type='global').order_by(Message.created_at.asc()).limit(100).all()
    return render_template('chat/room.html',
        room_type='global',
        room_id=0,
        room_name='Campus General Chat',
        messages=messages
    )

@chat_bp.route('/classroom/<int:classroom_id>')
@login_required
def classroom_chat(classroom_id):
    classroom = Classroom.query.get_or_404(classroom_id)
    is_teacher = current_user.id == classroom.teacher_id
    is_member = ClassroomMember.query.filter_by(
        classroom_id=classroom_id, student_id=current_user.id
    ).first() is not None
    if not is_teacher and not is_member:
        flash('You are not a member of this classroom.', 'danger')
        return redirect(url_for('chat.index'))
    messages = Message.query.filter_by(room_type='classroom', room_id=classroom_id).order_by(Message.created_at.asc()).limit(100).all()
    return render_template('chat/room.html',
        room_type='classroom',
        room_id=classroom_id,
        room_name=classroom.name,
        messages=messages
    )

@socketio.on('join')
def on_join(data):
    room = data.get('room')
    join_room(room)
    emit('status', {'msg': f'Joined room {room}'}, to=room)

@socketio.on('leave')
def on_leave(data):
    room = data.get('room')
    leave_room(room)

@socketio.on('send_message')
def handle_message(data):
    from flask_login import current_user
    from app import db
    from app.models import Message, User
    room = data.get('room', 'global')
    content = data.get('content', '').strip()
    if not content:
        return
    parts = room.split('_')
    room_type = parts[0]
    room_id = int(parts[1]) if len(parts) > 1 else 0
    msg = Message(
        room_type=room_type,
        room_id=room_id,
        sender_id=current_user.id,
        content=content
    )
    db.session.add(msg)
    db.session.commit()
    emit('receive_message', {
        'id': msg.id,
        'sender': current_user.username,
        'sender_role': current_user.role,
        'content': content,
        'timestamp': msg.created_at.strftime('%H:%M'),
        'is_mine': False
    }, to=room)
