from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models import Event, EventRegistration, Announcement, User
from app.campus import campus_bp

@campus_bp.route('/')
@login_required
def feed():
    events = Event.query.filter_by(status='approved').order_by(Event.date.asc()).all()
    announcements = Announcement.query.filter_by(status='approved').order_by(Announcement.created_at.desc()).limit(10).all()
    upcoming = Event.query.filter(
        Event.status == 'approved',
        Event.date >= datetime.utcnow()
    ).order_by(Event.date.asc()).limit(5).all()
    
    user_registrations = []
    if current_user.is_authenticated:
        user_registrations = [r.event_id for r in EventRegistration.query.filter_by(user_id=current_user.id).all()]
    
    dept_events = []
    if current_user.department:
        dept_events = Event.query.filter(
            Event.status == 'approved',
            Event.department == current_user.department,
            Event.date >= datetime.utcnow()
        ).order_by(Event.date.asc()).limit(3).all()
    
    return render_template('campus/feed.html',
        events=events,
        announcements=announcements,
        upcoming=upcoming,
        user_registrations=user_registrations,
        dept_events=dept_events
    )

@campus_bp.route('/events')
@login_required
def events():
    category = request.args.get('category', '')
    status_filter = request.args.get('status', 'approved')
    search = request.args.get('search', '')
    
    query = Event.query
    if category:
        query = query.filter_by(category=category)
    if status_filter == 'approved':
        query = query.filter_by(status='approved')
    if search:
        query = query.filter(Event.title.ilike(f'%{search}%'))
    
    events_list = query.order_by(Event.date.desc()).all()
    user_registrations = [r.event_id for r in EventRegistration.query.filter_by(user_id=current_user.id).all()]
    
    return render_template('campus/events.html',
        events=events_list,
        user_registrations=user_registrations,
        category=category,
        search=search
    )

@campus_bp.route('/events/create', methods=['GET', 'POST'])
@login_required
def create_event():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        date_str = request.form.get('date', '')
        location = request.form.get('location', '').strip()
        category = request.form.get('category', 'general')
        max_participants = request.form.get('max_participants', '')
        tags = request.form.get('tags', '').strip()
        department = request.form.get('department', '').strip()

        if not all([title, description, date_str]):
            flash('Title, description, and date are required.', 'danger')
            return render_template('campus/create_event.html')
        
        try:
            event_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Invalid date format.', 'danger')
            return render_template('campus/create_event.html')

        status = 'approved' if current_user.is_teacher() else 'pending'
        event = Event(
            title=title,
            description=description,
            date=event_date,
            location=location,
            category=category,
            max_participants=int(max_participants) if max_participants.isdigit() else None,
            tags=tags,
            department=department,
            organizer_id=current_user.id,
            status=status
        )
        db.session.add(event)
        db.session.commit()
        
        if status == 'pending':
            flash('Event submitted for teacher approval!', 'success')
        else:
            flash('Event created and published!', 'success')
        return redirect(url_for('campus.events'))
    
    return render_template('campus/create_event.html')

@campus_bp.route('/events/<int:event_id>')
@login_required
def event_detail(event_id):
    event = Event.query.get_or_404(event_id)
    is_registered = EventRegistration.query.filter_by(
        event_id=event_id, user_id=current_user.id
    ).first() is not None
    return render_template('campus/event_detail.html', event=event, is_registered=is_registered)

@campus_bp.route('/events/<int:event_id>/register', methods=['POST'])
@login_required
def register_event(event_id):
    event = Event.query.get_or_404(event_id)
    if event.status != 'approved':
        flash('This event is not available for registration.', 'danger')
        return redirect(url_for('campus.event_detail', event_id=event_id))
    if event.is_full():
        flash('This event is full.', 'danger')
        return redirect(url_for('campus.event_detail', event_id=event_id))
    existing = EventRegistration.query.filter_by(event_id=event_id, user_id=current_user.id).first()
    if existing:
        flash('You are already registered for this event.', 'warning')
        return redirect(url_for('campus.event_detail', event_id=event_id))
    reg = EventRegistration(event_id=event_id, user_id=current_user.id)
    db.session.add(reg)
    db.session.commit()
    flash('Successfully registered for the event!', 'success')
    return redirect(url_for('campus.event_detail', event_id=event_id))

@campus_bp.route('/events/<int:event_id>/unregister', methods=['POST'])
@login_required
def unregister_event(event_id):
    reg = EventRegistration.query.filter_by(event_id=event_id, user_id=current_user.id).first_or_404()
    db.session.delete(reg)
    db.session.commit()
    flash('Unregistered from event.', 'info')
    return redirect(url_for('campus.event_detail', event_id=event_id))

@campus_bp.route('/moderation')
@login_required
def moderation():
    if not current_user.is_teacher():
        flash('Access denied. Teachers only.', 'danger')
        return redirect(url_for('campus.feed'))
    pending_events = Event.query.filter_by(status='pending').order_by(Event.created_at.desc()).all()
    pending_announcements = Announcement.query.filter_by(status='pending').order_by(Announcement.created_at.desc()).all()
    return render_template('campus/moderation.html',
        pending_events=pending_events,
        pending_announcements=pending_announcements
    )

@campus_bp.route('/events/<int:event_id>/moderate', methods=['POST'])
@login_required
def moderate_event(event_id):
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('campus.feed'))
    event = Event.query.get_or_404(event_id)
    action = request.form.get('action')
    if action == 'approve':
        event.status = 'approved'
        event.approved_at = datetime.utcnow()
        event.approved_by = current_user.id
        flash(f'Event "{event.title}" approved!', 'success')
    elif action == 'reject':
        event.status = 'rejected'
        flash(f'Event "{event.title}" rejected.', 'warning')
    db.session.commit()
    return redirect(url_for('campus.moderation'))

@campus_bp.route('/announcements/create', methods=['GET', 'POST'])
@login_required
def create_announcement():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        priority = request.form.get('priority', 'normal')
        if not all([title, content]):
            flash('Title and content are required.', 'danger')
            return render_template('campus/create_announcement.html')
        
        status = 'approved' if current_user.is_teacher() else 'pending'
        ann = Announcement(
            title=title,
            content=content,
            priority=priority,
            author_id=current_user.id,
            status=status
        )
        db.session.add(ann)
        db.session.commit()
        if status == 'pending':
            flash('Announcement submitted for approval!', 'success')
        else:
            flash('Announcement published!', 'success')
        return redirect(url_for('campus.feed'))
    return render_template('campus/create_announcement.html')

@campus_bp.route('/announcements/<int:ann_id>/moderate', methods=['POST'])
@login_required
def moderate_announcement(ann_id):
    if not current_user.is_teacher():
        flash('Access denied.', 'danger')
        return redirect(url_for('campus.feed'))
    ann = Announcement.query.get_or_404(ann_id)
    action = request.form.get('action')
    if action == 'approve':
        ann.status = 'approved'
        ann.approved_at = datetime.utcnow()
        ann.approved_by = current_user.id
        flash(f'Announcement approved!', 'success')
    elif action == 'reject':
        ann.status = 'rejected'
        flash('Announcement rejected.', 'warning')
    db.session.commit()
    return redirect(url_for('campus.moderation'))

@campus_bp.route('/my-events')
@login_required
def my_events():
    if current_user.is_teacher():
        events_list = Event.query.filter_by(organizer_id=current_user.id).order_by(Event.created_at.desc()).all()
    else:
        regs = EventRegistration.query.filter_by(user_id=current_user.id).all()
        event_ids = [r.event_id for r in regs]
        events_list = Event.query.filter(Event.id.in_(event_ids)).all()
    return render_template('campus/my_events.html', events=events_list)
