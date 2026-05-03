from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from datetime import datetime, timedelta, time
import calendar
from app.models import Event, EventRegistration
from app.calendar import calendar_bp

# Class routine — day abbreviation → list of (start_time, end_time) tuples
CLASS_ROUTINE = {
    'Sun': [
        (time(11, 15), time(12, 45)),
        (time(13, 15), time(14, 45)),
        (time(14, 45), time(16, 15)),
    ],
    'Mon': [
        (time(11, 15), time(12, 45)),
        (time(13, 15), time(14, 45)),
    ],
    'Tue': [
        (time(8,  15), time(9,  45)),
        (time(9,  45), time(11, 15)),
        (time(11, 15), time(12, 45)),
    ],
    'Wed': [
        (time(8,  15), time(9,  45)),
        (time(9,  45), time(11, 15)),
        (time(11, 15), time(12, 45)),
    ],
    'Thu': [
        (time(8,  15), time(9,  45)),
        (time(9,  45), time(11, 15)),
        (time(11, 15), time(12, 45)),
    ],
    'Fri': [],
    'Sat': [],
}

EVENT_DURATION_MINUTES = 120  # assume 2-hour events

def _overlap_minutes(ev_start: time, ev_end: time, cls_start: time, cls_end: time) -> int:
    """Return overlapping minutes between two time ranges."""
    latest_start = max(ev_start, cls_start)
    earliest_end = min(ev_end, cls_end)
    if earliest_end > latest_start:
        diff = datetime.combine(datetime.today(), earliest_end) - \
               datetime.combine(datetime.today(), latest_start)
        return int(diff.total_seconds() // 60)
    return 0

def clash_level(event_dt: datetime) -> str:
    """Return 'green', 'yellow', or 'red' based on class routine overlap."""
    day_abbr = event_dt.strftime('%a')  # 'Sun', 'Mon', …
    classes = CLASS_ROUTINE.get(day_abbr, [])
    if not classes:
        return 'green'
    ev_start = event_dt.time()
    ev_end_dt = event_dt + timedelta(minutes=EVENT_DURATION_MINUTES)
    ev_end = ev_end_dt.time()
    total_overlap = sum(_overlap_minutes(ev_start, ev_end, cs, ce) for cs, ce in classes)
    if total_overlap == 0:
        return 'green'
    elif total_overlap < 90:
        return 'yellow'
    else:
        return 'red'

def _worst_level(levels):
    """Return the worst clash level from a list."""
    if 'red' in levels:
        return 'red'
    if 'yellow' in levels:
        return 'yellow'
    return 'green'

@calendar_bp.route('/')
@login_required
def index():
    now = datetime.utcnow()
    year  = int(request.args.get('year',  now.year))
    month = int(request.args.get('month', now.month))

    # clamp valid ranges
    year  = max(2020, min(year,  2099))
    month = max(1,    min(month, 12))

    first_day = datetime(year, month, 1)
    if month == 12:
        last_day = datetime(year + 1, 1, 1) - timedelta(seconds=1)
    else:
        last_day = datetime(year, month + 1, 1) - timedelta(seconds=1)

    user_reg_ids = [r.event_id for r in
                    EventRegistration.query.filter_by(user_id=current_user.id).all()]

    month_events = Event.query.filter(
        Event.status == 'approved',
        Event.date >= first_day,
        Event.date <= last_day
    ).order_by(Event.date.asc()).all()

    events_by_day = {}
    for ev in month_events:
        day = ev.date.day
        level = clash_level(ev.date)
        if day not in events_by_day:
            events_by_day[day] = []
        events_by_day[day].append({
            'id':         ev.id,
            'title':      ev.title,
            'category':   ev.category,
            'time':       ev.date.strftime('%I:%M %p'),
            'registered': ev.id in user_reg_ids,
            'clash':      level,
        })

    # Compute worst clash per day (for border color)
    day_clash = {
        d: _worst_level([e['clash'] for e in evs])
        for d, evs in events_by_day.items()
    }

    cal_grid    = calendar.monthcalendar(year, month)
    prev_month  = month - 1 if month > 1  else 12
    prev_year   = year      if month > 1  else year - 1
    next_month  = month + 1 if month < 12 else 1
    next_year   = year      if month < 12 else year + 1

    my_upcoming = []
    if user_reg_ids:
        my_upcoming = Event.query.filter(
            Event.id.in_(user_reg_ids),
            Event.date >= now
        ).order_by(Event.date.asc()).limit(10).all()

    return render_template('calendar/index.html',
        cal=cal_grid,
        year=year,  month=month,
        month_name=calendar.month_name[month],
        events_by_day=events_by_day,
        day_clash=day_clash,
        today=(now.day if now.year == year and now.month == month else None),
        prev_month=prev_month, prev_year=prev_year,
        next_month=next_month, next_year=next_year,
        my_upcoming=my_upcoming,
        user_reg_ids=user_reg_ids,
    )

@calendar_bp.route('/day')
@login_required
def day_events():
    now   = datetime.utcnow()
    year  = int(request.args.get('year',  now.year))
    month = int(request.args.get('month', now.month))
    day   = int(request.args.get('day',   now.day))
    date      = datetime(year, month, day)
    next_date = date + timedelta(days=1)
    events = Event.query.filter(
        Event.status == 'approved',
        Event.date >= date,
        Event.date <  next_date
    ).order_by(Event.date.asc()).all()
    user_reg_ids = [r.event_id for r in
                    EventRegistration.query.filter_by(user_id=current_user.id).all()]
    # add clash info
    events_with_clash = [(e, clash_level(e.date)) for e in events]
    return render_template('calendar/day.html',
        events_with_clash=events_with_clash,
        date=date,
        user_reg_ids=user_reg_ids,
    )

@calendar_bp.route('/api/events')
@login_required
def api_events():
    user_reg_ids = [r.event_id for r in
                    EventRegistration.query.filter_by(user_id=current_user.id).all()]
    events = Event.query.filter_by(status='approved').all()
    return jsonify([{
        'id':         e.id,
        'title':      e.title,
        'date':       e.date.strftime('%Y-%m-%d'),
        'category':   e.category,
        'registered': e.id in user_reg_ids,
        'clash':      clash_level(e.date),
    } for e in events])
