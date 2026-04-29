from app import create_app, db, bcrypt
from app.models import User, Event, Announcement
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    db.create_all()
    
    if User.query.count() > 0:
        print("Database already seeded.")
    else:
        print("Seeding database...")

        teacher = User(
            username='prof_masud',
            email='masud@bubt.edu.bd',
            password_hash=bcrypt.generate_password_hash('password123').decode('utf-8'),
            role='teacher',
            department='CSE',
            bio='Assistant Professor, Dept. of CSE, BUBT'
        )
        db.session.add(teacher)

        students = []
        for i, (name, email, intake) in enumerate([
            ('tamjid_hridoy', 'tamjid@bubt.edu.bd', '58th'),
            ('musfika_jannat', 'musfika@bubt.edu.bd', '58th'),
            ('farjana_haque', 'farjana@bubt.edu.bd', '58th'),
            ('asfaque_akhond', 'asfaque@bubt.edu.bd', '58th'),
            ('nafisa_ulfat', 'nafisa@bubt.edu.bd', '58th'),
        ]):
            s = User(
                username=name,
                email=email,
                password_hash=bcrypt.generate_password_hash('password123').decode('utf-8'),
                role='student',
                department='CSE',
                intake=intake
            )
            db.session.add(s)
            students.append(s)

        db.session.flush()

        events = [
            Event(
                title='AI & Machine Learning Workshop',
                description='A hands-on workshop exploring modern AI and ML techniques. Learn about neural networks, deep learning, and practical applications in Python. All CSE students are encouraged to attend.',
                date=datetime.utcnow() + timedelta(days=7),
                location='Lab 301, BUBT',
                category='workshop',
                status='approved',
                organizer_id=teacher.id,
                department='CSE',
                tags='AI, Machine Learning, Python',
                max_participants=50,
                approved_by=teacher.id,
                approved_at=datetime.utcnow()
            ),
            Event(
                title='Inter-Department Cricket Tournament',
                description='Annual inter-department cricket tournament. Form your team and register! Matches will be held over 3 days.',
                date=datetime.utcnow() + timedelta(days=14),
                location='BUBT Sports Ground',
                category='sports',
                status='approved',
                organizer_id=teacher.id,
                tags='Cricket, Sports, Tournament',
                max_participants=100,
                approved_by=teacher.id,
                approved_at=datetime.utcnow()
            ),
            Event(
                title='Cultural Fest 2025 - Rang e BUBT',
                description='Celebrate the rich cultural diversity of BUBT! Music, dance, art exhibitions, photography contest, and food stalls. Come and participate!',
                date=datetime.utcnow() + timedelta(days=21),
                location='BUBT Auditorium',
                category='cultural',
                status='approved',
                organizer_id=teacher.id,
                tags='Culture, Music, Dance, Art',
                approved_by=teacher.id,
                approved_at=datetime.utcnow()
            ),
            Event(
                title='Guest Lecture: Industry 4.0',
                description='Senior software engineer from a leading tech company will deliver a lecture on Industry 4.0 trends, IoT, and career opportunities in tech.',
                date=datetime.utcnow() + timedelta(days=5),
                location='Seminar Hall, Floor 5',
                category='seminar',
                status='approved',
                organizer_id=teacher.id,
                department='CSE',
                tags='Industry, Career, IoT',
                approved_by=teacher.id,
                approved_at=datetime.utcnow()
            ),
            Event(
                title='CSE Club Annual Hackathon',
                description='24-hour hackathon for CSE students. Form teams of 3-5 members and build something amazing! Prizes worth 50,000 BDT.',
                date=datetime.utcnow() + timedelta(days=30),
                location='CSE Labs, BUBT',
                category='academic',
                status='pending',
                organizer_id=students[0].id,
                department='CSE',
                tags='Hackathon, Programming, Competition'
            )
        ]
        for e in events:
            db.session.add(e)

        announcements = [
            Announcement(
                title='Mid-Term Exam Schedule Released',
                content='The mid-term examination schedule for Fall 2025 has been published. All students are advised to check the exam portal and prepare accordingly. Exams begin from next Monday.',
                author_id=teacher.id,
                status='approved',
                priority='urgent',
                approved_by=teacher.id,
                approved_at=datetime.utcnow()
            ),
            Announcement(
                title='Library Extended Hours During Exam Period',
                content='The BUBT library will remain open until 10 PM during the mid-term examination period. Students can use the study halls and digital resources.',
                author_id=teacher.id,
                status='approved',
                priority='normal',
                approved_by=teacher.id,
                approved_at=datetime.utcnow()
            ),
            Announcement(
                title='Workshop Registration Open',
                content='Registration for the upcoming AI & Machine Learning workshop is now open. Please register through the Events section before seats fill up.',
                author_id=students[1].id,
                status='pending',
                priority='normal'
            )
        ]
        for a in announcements:
            db.session.add(a)

        db.session.commit()
        print("✓ Database seeded successfully!")
        print("\nDemo accounts (password: password123):")
        print("  Teacher: masud@bubt.edu.bd")
        print("  Student: tamjid@bubt.edu.bd")
        print("  Student: musfika@bubt.edu.bd")
