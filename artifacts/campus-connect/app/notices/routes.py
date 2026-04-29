from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from datetime import datetime
from app import db
from app.models import Announcement
from app.notices import notices_bp

@notices_bp.route('/')
@login_required
def index():
    priority = request.args.get('priority', '')
    search = request.args.get('search', '')
    query = Announcement.query.filter_by(status='approved')
    if priority:
        query = query.filter_by(priority=priority)
    if search:
        query = query.filter(Announcement.title.ilike(f'%{search}%'))
    notices = query.order_by(Announcement.created_at.desc()).all()
    urgent = Announcement.query.filter_by(status='approved', priority='urgent').order_by(Announcement.created_at.desc()).limit(3).all()
    return render_template('notices/index.html', notices=notices, urgent=urgent, priority=priority, search=search)

@notices_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        priority = request.form.get('priority', 'normal')
        if not all([title, content]):
            flash('Title and content are required.', 'danger')
            return render_template('notices/create.html')
        status = 'approved' if current_user.is_teacher() else 'pending'
        ann = Announcement(
            title=title, content=content,
            priority=priority, author_id=current_user.id, status=status
        )
        db.session.add(ann)
        db.session.commit()
        flash('Notice published!' if status == 'approved' else 'Notice submitted for approval.', 'success')
        return redirect(url_for('notices.index'))
    return render_template('notices/create.html')
