from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from flask_socketio import emit, join_room, leave_room
from datetime import datetime
from app import db, socketio
from app.models import Message, Classroom, ClassroomMember, Event
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
        room_type='global', room_id=0,
        room_name='Campus General Chat',
        room_icon='global', messages=messages
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
        room_type='classroom', room_id=classroom_id,
        room_name=classroom.name, room_icon='classroom',
        messages=messages
    )

@chat_bp.route('/ai')
@login_required
def ai_chat():
    return render_template('chat/ai.html')

@chat_bp.route('/ai/ask', methods=['POST'])
@login_required
def ai_ask():
    question = request.json.get('question', '').strip().lower()
    answer = generate_ai_response(question)
    return jsonify({'answer': answer})

def generate_ai_response(question):
    from app.models import Event, Classroom, ClassroomMember, Announcement
    from datetime import datetime, timedelta
    now = datetime.utcnow()

    if any(w in question for w in ['event', 'events', 'happening', 'upcoming', 'schedule']):
        events = Event.query.filter(
            Event.status == 'approved',
            Event.date >= now
        ).order_by(Event.date.asc()).limit(5).all()
        if events:
            response = "📅 **Upcoming events on campus:**\n\n"
            for e in events:
                response += f"• **{e.title}** — {e.date.strftime('%B %d at %I:%M %p')}"
                if e.location:
                    response += f" at {e.location}"
                response += "\n"
            return response
        return "No upcoming events found right now."

    if any(w in question for w in ['notice', 'announcement', 'notice']):
        notices = Announcement.query.filter_by(status='approved').order_by(Announcement.created_at.desc()).limit(3).all()
        if notices:
            response = "📢 **Latest campus notices:**\n\n"
            for n in notices:
                response += f"• **{n.title}**\n  {n.content[:100]}...\n\n"
            return response
        return "No recent notices found."

    if any(w in question for w in ['classroom', 'class', 'course', 'join']):
        return "📚 **Classrooms:** Teachers create classrooms with a unique code. Students can join by going to Classroom → Join and entering the code. You can view materials, join chats, and track assignments there."

    if any(w in question for w in ['register', 'sign up', 'enroll']):
        return "✅ **Registering for events:** Go to the Events page, browse available events, and click 'Register'. You can track all your registrations in My Calendar."

    if any(w in question for w in ['chat', 'message', 'talk', 'communicate']):
        return "💬 **Chat options available:**\n• **Campus Chat** — Talk with all students and teachers\n• **Classroom Chat** — Chat with your class group\n• **AI Assistant** — That's me! Ask anything about campus life."

    if any(w in question for w in ['calendar', 'my schedule', 'my events']):
        return "📅 **My Calendar** shows all events you've registered for in a monthly calendar view. Click any date to see events happening that day."

    if any(w in question for w in ['help', 'what can you do', 'features', 'how']):
        return ("🤖 **I'm CampusConnect AI Assistant!** I can help you with:\n\n"
                "• 📅 Finding upcoming events\n"
                "• 📢 Latest campus notices\n"
                "• 📚 How to use classrooms\n"
                "• 💬 Chat features\n"
                "• ✅ Event registration\n"
                "• 📆 Your calendar\n\n"
                "Just ask me anything about campus life!")

    if any(w in question for w in ['hello', 'hi', 'hey', 'good morning', 'good afternoon']):
        return "👋 Hello! I'm the CampusConnect AI Assistant. I can help you find events, announcements, classroom info, and more. What would you like to know?"

    if any(w in question for w in ['bubt', 'university', 'campus', 'department']):
        return "🏫 **BUBT (Bangladesh University of Business and Technology)** — CampusConnect Hub is designed specifically for BUBT students and teachers to manage academic and social campus life in one place."

    if any(w in question for w in ['teacher', 'professor', 'faculty']):
        return "👨‍🏫 **Teachers on CampusConnect** can: create and manage classrooms, post materials, approve/reject student events and announcements, and create their own events directly."

    if any(w in question for w in ['student', 'students']):
        return "👩‍🎓 **Students on CampusConnect** can: join classrooms with codes, register for events, post content for approval, chat with classmates, and track everything on their personal calendar."

    return ("🤔 I'm not sure about that specific question. I can help you with:\n"
            "• Upcoming events and schedules\n"
            "• Campus notices and announcements\n"
            "• Classroom and academic info\n"
            "• How to use CampusConnect features\n\n"
            "Try asking something like 'What events are coming up?' or 'How do I join a classroom?'")

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
    from app import db
    from app.models import Message
    room = data.get('room', 'global')
    content = data.get('content', '').strip()
    if not content:
        return
    parts = room.split('_')
    room_type = parts[0]
    room_id = int(parts[1]) if len(parts) > 1 else 0
    msg = Message(
        room_type=room_type, room_id=room_id,
        sender_id=current_user.id, content=content
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
