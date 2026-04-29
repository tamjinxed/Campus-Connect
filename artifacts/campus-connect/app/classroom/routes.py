import random
import string
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models import Classroom, ClassroomMember, Material
from app.classroom import classroom_bp

def generate_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

@classroom_bp.route('/')
@login_required
def index():
    if current_user.is_teacher():
        classrooms = Classroom.query.filter_by(teacher_id=current_user.id).order_by(Classroom.created_at.desc()).all()
    else:
        memberships = ClassroomMember.query.filter_by(student_id=current_user.id).all()
        classroom_ids = [m.classroom_id for m in memberships]
        classrooms = Classroom.query.filter(Classroom.id.in_(classroom_ids)).all()
    return render_template('classroom/index.html', classrooms=classrooms)

@classroom_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    if not current_user.is_teacher():
        flash('Only teachers can create classrooms.', 'danger')
        return redirect(url_for('classroom.index'))
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        department = request.form.get('department', '').strip()
        section = request.form.get('section', '').strip()
        if not name:
            flash('Classroom name is required.', 'danger')
            return render_template('classroom/create.html')
        code = generate_code()
        while Classroom.query.filter_by(code=code).first():
            code = generate_code()
        classroom = Classroom(
            name=name,
            code=code,
            description=description,
            department=department,
            section=section,
            teacher_id=current_user.id
        )
        db.session.add(classroom)
        db.session.commit()
        flash(f'Classroom created! Share the code: {code}', 'success')
        return redirect(url_for('classroom.view', classroom_id=classroom.id))
    return render_template('classroom/create.html')

@classroom_bp.route('/join', methods=['GET', 'POST'])
@login_required
def join():
    if current_user.is_teacher():
        flash('Teachers cannot join classrooms as students.', 'warning')
        return redirect(url_for('classroom.index'))
    if request.method == 'POST':
        code = request.form.get('code', '').strip().upper()
        classroom = Classroom.query.filter_by(code=code).first()
        if not classroom:
            flash('Invalid classroom code.', 'danger')
            return render_template('classroom/join.html')
        existing = ClassroomMember.query.filter_by(
            classroom_id=classroom.id, student_id=current_user.id
        ).first()
        if existing:
            flash('You are already a member of this classroom.', 'warning')
            return redirect(url_for('classroom.view', classroom_id=classroom.id))
        member = ClassroomMember(classroom_id=classroom.id, student_id=current_user.id)
        db.session.add(member)
        db.session.commit()
        flash(f'Joined classroom "{classroom.name}"!', 'success')
        return redirect(url_for('classroom.view', classroom_id=classroom.id))
    return render_template('classroom/join.html')

@classroom_bp.route('/<int:classroom_id>')
@login_required
def view(classroom_id):
    classroom = Classroom.query.get_or_404(classroom_id)
    is_teacher = current_user.id == classroom.teacher_id
    is_member = ClassroomMember.query.filter_by(
        classroom_id=classroom_id, student_id=current_user.id
    ).first() is not None
    if not is_teacher and not is_member:
        flash('You are not a member of this classroom.', 'danger')
        return redirect(url_for('classroom.index'))
    materials = Material.query.filter_by(classroom_id=classroom_id).order_by(Material.created_at.desc()).all()
    members = ClassroomMember.query.filter_by(classroom_id=classroom_id).all()
    return render_template('classroom/view.html',
        classroom=classroom,
        materials=materials,
        members=members,
        is_teacher=is_teacher
    )

@classroom_bp.route('/<int:classroom_id>/material/add', methods=['GET', 'POST'])
@login_required
def add_material(classroom_id):
    classroom = Classroom.query.get_or_404(classroom_id)
    if current_user.id != classroom.teacher_id:
        flash('Only the teacher can add materials.', 'danger')
        return redirect(url_for('classroom.view', classroom_id=classroom_id))
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        content = request.form.get('content', '').strip()
        material_type = request.form.get('material_type', 'note')
        if not title:
            flash('Title is required.', 'danger')
            return render_template('classroom/add_material.html', classroom=classroom)
        material = Material(
            classroom_id=classroom_id,
            title=title,
            content=content,
            material_type=material_type,
            uploaded_by=current_user.id
        )
        db.session.add(material)
        db.session.commit()
        flash('Material added successfully!', 'success')
        return redirect(url_for('classroom.view', classroom_id=classroom_id))
    return render_template('classroom/add_material.html', classroom=classroom)

@classroom_bp.route('/<int:classroom_id>/material/<int:material_id>/delete', methods=['POST'])
@login_required
def delete_material(classroom_id, material_id):
    classroom = Classroom.query.get_or_404(classroom_id)
    if current_user.id != classroom.teacher_id:
        flash('Access denied.', 'danger')
        return redirect(url_for('classroom.view', classroom_id=classroom_id))
    material = Material.query.get_or_404(material_id)
    db.session.delete(material)
    db.session.commit()
    flash('Material deleted.', 'info')
    return redirect(url_for('classroom.view', classroom_id=classroom_id))

@classroom_bp.route('/<int:classroom_id>/leave', methods=['POST'])
@login_required
def leave(classroom_id):
    member = ClassroomMember.query.filter_by(
        classroom_id=classroom_id, student_id=current_user.id
    ).first_or_404()
    db.session.delete(member)
    db.session.commit()
    flash('Left classroom.', 'info')
    return redirect(url_for('classroom.index'))
