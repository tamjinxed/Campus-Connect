import os
from app import create_app, db, socketio
from app.models import User, Event, Classroom, Message, Announcement

app = create_app()

@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Event': Event, 'Classroom': Classroom}

def seed_future_events():
    """Add spread-out future events so every month May–Sep has content."""
    from datetime import datetime
    teacher = User.query.filter_by(role='teacher').first()
    if not teacher:
        return

    # Events keyed by absolute date+time so we never double-insert
    planned = [
        # ------- May -------
        dict(title='Python Web Dev Bootcamp',
             description='Intensive two-day bootcamp covering Django and Flask. Build and deploy a real project from scratch.',
             date=datetime(2026, 5, 10, 8, 0),   # Sun 08:00 → no class at 8 AM Sun → green
             location='Lab 402, BUBT', category='workshop', department='CSE',
             tags='Python, Django, Flask', max_participants=40),
        dict(title='CSE Blood Donation Camp',
             description='Annual blood donation drive organised by CSE Club. Certificates provided to all donors.',
             date=datetime(2026, 5, 17, 11, 30),  # Sun 11:30 → 11:15-12:45 class → red
             location='Cafeteria Hall', category='club',
             tags='Social, Health'),
        dict(title='Freshers Orientation 2026',
             description='Welcome programme for new BUBT students. Campus tour, faculty introductions, and Q&A session.',
             date=datetime(2026, 5, 25, 14, 0),   # Mon 14:00 → 13:15-14:45 class → yellow
             location='BUBT Auditorium', category='academic',
             tags='Orientation, Freshers'),
        # ------- June -------
        dict(title='Web3 & Blockchain Seminar',
             description='Explore decentralised technologies, smart contracts, and the future of the internet with industry experts.',
             date=datetime(2026, 6, 7, 11, 0),    # Sun 11:00 → overlaps 11:15-12:45 → yellow
             location='Seminar Hall, Floor 5', category='seminar', department='CSE',
             tags='Blockchain, Web3, Crypto', max_participants=80),
        dict(title='Inter-Uni Math Olympiad',
             description='BUBT hosts the regional round of the university mathematics olympiad. All departments welcome.',
             date=datetime(2026, 6, 13, 9, 0),    # Sat 09:00 → no class Sat → green
             location='Exam Hall A', category='academic',
             tags='Math, Competition'),
        dict(title='Photography Walk – Old Dhaka',
             description='Join the Photography Club for a guided street photography walk through Old Dhaka heritage sites.',
             date=datetime(2026, 6, 20, 7, 30),   # Sat 07:30 → no class Sat → green
             location='Meet at Main Gate', category='club',
             tags='Photography, Heritage, Art'),
        dict(title='Robotics Workshop – Arduino Basics',
             description='Hands-on session building simple robots with Arduino. Components provided. No prior experience needed.',
             date=datetime(2026, 6, 28, 13, 15),  # Sun 13:15 → 13:15-14:45 class → red
             location='EEE Lab 2, Floor 3', category='workshop', department='CSE',
             tags='Robotics, Arduino, Hardware', max_participants=30),
        # ------- July -------
        dict(title='BUBT Science Fair 2026',
             description='Annual science and technology exhibition. Students showcase projects, prototypes, and research work.',
             date=datetime(2026, 7, 5, 10, 0),    # Sun 10:00 → before 11:15 class → green
             location='BUBT Ground Floor Hall', category='academic',
             tags='Science, Research, Exhibition', max_participants=200),
        dict(title='Career Fair & Industry Expo',
             description='30+ companies on campus for internship and full-time hiring. Bring your CV. All departments welcome.',
             date=datetime(2026, 7, 12, 10, 0),   # Sun 10:00 → before 11:15 → green
             location='BUBT Convention Centre', category='academic',
             tags='Career, Jobs, Internship', max_participants=500),
        dict(title='Basketball 3×3 Street Tournament',
             description='Fast-paced 3-on-3 basketball. Open to all students. Register in groups of 3.',
             date=datetime(2026, 7, 19, 14, 45),  # Sun 14:45 → 14:45-16:15 class → red
             location='BUBT Basketball Court', category='sports',
             tags='Basketball, Sports, Tournament'),
        dict(title='Data Science with R Workshop',
             description='Introduction to data analysis, visualisation, and machine learning using the R language.',
             date=datetime(2026, 7, 25, 9, 45),   # Fri 09:45 → no class Fri → green
             location='Lab 301, BUBT', category='workshop', department='CSE',
             tags='Data Science, R, Statistics', max_participants=35),
        # ------- August -------
        dict(title='Independence Day Cultural Gala',
             description='Grand cultural evening to celebrate Bangladesh Independence Day with performances, food, and art.',
             date=datetime(2026, 8, 2, 18, 0),    # Sun 18:00 → after all classes → green
             location='BUBT Auditorium', category='cultural',
             tags='Culture, National Day, Music'),
        dict(title='Final Year Project Symposium',
             description='Final year CSE students present their capstone projects to faculty and industry judges.',
             date=datetime(2026, 8, 9, 9, 0),     # Sun 09:00 → before 11:15 class → green
             location='Seminar Hall', category='academic', department='CSE',
             tags='FYP, Research, Presentation'),
        dict(title='Cybersecurity CTF Challenge',
             description='Capture the Flag competition covering web security, cryptography, and binary exploitation.',
             date=datetime(2026, 8, 16, 11, 15),  # Sun 11:15 → exact 11:15-12:45 class → red
             location='Online + BUBT CSE Lab', category='academic', department='CSE',
             tags='Cybersecurity, CTF, Hacking', max_participants=60),
        dict(title='Volunteer Day – Campus Cleanup',
             description='Join fellow students in a campus beautification and tree-planting drive.',
             date=datetime(2026, 8, 22, 8, 0),    # Sat 08:00 → no class Sat → green
             location='BUBT Campus', category='club',
             tags='Volunteer, Environment'),
        # ------- September -------
        dict(title='Thesis Writing & Research Methods',
             description='Workshop on academic writing, citation management, and research methodology for final-year students.',
             date=datetime(2026, 9, 5, 13, 15),   # Sat 13:15 → no class Sat → green
             location='Library Seminar Room', category='seminar', department='CSE',
             tags='Research, Writing, Thesis', max_participants=50),
        dict(title='Annual Sports Gala 2026',
             description='Multi-sport competition across all departments: football, cricket, chess, table tennis, and athletics.',
             date=datetime(2026, 9, 13, 9, 45),   # Sun 09:45 → before 11:15 class → green
             location='BUBT Sports Complex', category='sports',
             tags='Sports, Gala, Competition'),
        dict(title='Tech Talk: AI in Healthcare',
             description='Guest lecture by Dr. Rahman on AI applications in medical diagnosis, drug discovery, and patient care.',
             date=datetime(2026, 9, 20, 11, 15),  # Sun 11:15 → exact 11:15-12:45 class → red
             location='Seminar Hall, Floor 5', category='seminar', department='CSE',
             tags='AI, Healthcare, Medical', max_participants=120),
    ]

    existing_titles = {e.title for e in Event.query.all()}
    added = 0
    for p in planned:
        if p['title'] in existing_titles:
            continue
        ev = Event(
            title=p['title'],
            description=p['description'],
            date=p['date'],
            location=p.get('location', ''),
            category=p.get('category', 'general'),
            department=p.get('department', ''),
            tags=p.get('tags', ''),
            max_participants=p.get('max_participants'),
            organizer_id=teacher.id,
            status='approved',
            approved_by=teacher.id,
            approved_at=datetime.utcnow(),
        )
        db.session.add(ev)
        added += 1
    if added:
        db.session.commit()
        print(f'✓ Added {added} future events across May–September 2026.')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    with app.app_context():
        db.create_all()
        seed_future_events()
    socketio.run(app, host='0.0.0.0', port=port, debug=False, allow_unsafe_werkzeug=True)
