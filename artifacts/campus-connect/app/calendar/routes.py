from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import calendar
from app.models import Event, EventRegistration
from app.calendar import calendar_bp

@calendar_bp.route('/')
@login_required
def index():
    now = datetime.utcnow()
    year = int(request.args.get('year', now.year))
    month = int(request.args.get('month', now.month))

    first_day = datetime(year, month, 1)
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(days=1)

    user_reg_ids = [r.event_id for r in EventRegistration.query.filter_by(user_id=current_user.id).all()]
    month_events = Event.query.filter(
        Event.status == 'approved',
        Event.date >= first_day,
        Event.date <= last_day
    ).order_by(Event.date.asc()).all()

    events_by_day = {}
    for ev in month_events:
        day = ev.date.day
        if day not in events_by_day:
            events_by_day[day] = []
        events_by_day[day].append({
            'id': ev.id,
            'title': ev.title,
            'category': ev.category,
            'time': ev.date.strftime('%I:%M %p'),
            'registered': ev.id in user_reg_ids
        })

    cal = calendar.monthcalendar(year, month)
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    my_upcoming = Event.query.filter(
        Event.id.in_(user_reg_ids),
        Event.date >= datetime.utcnow()
    ).order_by(Event.date.asc()).limit(10).all() if user_reg_ids else []

    return render_template('calendar/index.html',
        cal=cal,
        year=year, month=month,
        month_name=calendar.month_name[month],
        events_by_day=events_by_day,
        today=now.day if now.year == year and now.month == month else None,
        prev_month=prev_month, prev_year=prev_year,
        next_month=next_month, next_year=next_year,
        my_upcoming=my_upcoming,
        user_reg_ids=user_reg_ids
    )

@calendar_bp.route('/day')
@login_required
def day_events():
    year = int(request.args.get('year', datetime.utcnow().year))
    month = int(request.args.get('month', datetime.utcnow().month))
    day = int(request.args.get('day', datetime.utcnow().day))
    date = datetime(year, month, day)
    next_date = date + timedelta(days=1)
    events = Event.query.filter(
        Event.status == 'approved',
        Event.date >= date,
        Event.date < next_date
    ).order_by(Event.date.asc()).all()
    user_reg_ids = [r.event_id for r in EventRegistration.query.filter_by(user_id=current_user.id).all()]
    return render_template('calendar/day.html',
        events=events, date=date, user_reg_ids=user_reg_ids
    )

@calendar_bp.route('/api/events')
@login_required
def api_events():
    user_reg_ids = [r.event_id for r in EventRegistration.query.filter_by(user_id=current_user.id).all()]
    events = Event.query.filter_by(status='approved').all()
    return jsonify([{
        'id': e.id,
        'title': e.title,
        'date': e.date.strftime('%Y-%m-%d'),
        'category': e.category,
        'registered': e.id in user_reg_ids
    } for e in events])
