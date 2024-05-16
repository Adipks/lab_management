from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://root:abdthebest17@localhost/lab'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = 'your_secret_key'  # Change this to a secure random key

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# User model
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # student, professor, research_student, lab_assistant

# Student model
class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    roll_no = db.Column(db.String(9), unique=True, nullable=False)
    department = db.Column(db.String(50), nullable=False)
    semester = db.Column(db.Integer, nullable=False)

# Research Student model
class ResearchStudent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)
    roll_no = db.Column(db.String(10), unique=True, nullable=False)
    department = db.Column(db.String(50), nullable=False)

# Faculty model for Professors and Lab Assistants
class Faculty(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    faculty_name = db.Column(db.String(50), nullable=False)
    faculty_id = db.Column(db.String(10), unique=True, nullable=False)
    course_no = db.Column(db.String(10), nullable=False)
    department = db.Column(db.String(50), nullable=False)


class Lab(db.Model):
    lab_type = db.Column(db.String(255), nullable=False)
    lab_no = db.Column(db.Integer, primary_key=True)
    lab_assistant = db.Column(db.String(255), nullable=False)
    is_available = db.Column(db.String(10), nullable=False)


class Course(db.Model):
    course_no = db.Column(db.String(50), primary_key=True)
    course_name = db.Column(db.String(255), nullable=False)
    professor_id = db.Column(db.Integer, nullable=False)
    teaching_assistant = db.Column(db.String(255))

class LabCourse(db.Model):
    lab_no = db.Column(db.Integer, primary_key=True)
    course_no = db.Column(db.String(50), db.ForeignKey('course.course_no'), primary_key=True)    

class Project(db.Model):
    project_name = db.Column(db.String(255), nullable=False)
    project_id = db.Column(db.Integer, primary_key=True)
    lab_no = db.Column(db.Integer, db.ForeignKey('lab.lab_no'))

class Equipment(db.Model):
    equipment_name = db.Column(db.String(255), nullable=False)
    equipment_id = db.Column(db.String(50), primary_key=True)
    expiry_date = db.Column(db.Date)
    lab_no = db.Column(db.Integer, db.ForeignKey('lab.lab_no'))
    maintenance = db.Column(db.Date)

class FundedBy(db.Model):
    company_institute = db.Column(db.String(255), nullable=False)
    fund_id = db.Column(db.String(50), primary_key=True)
    amount = db.Column(db.Integer, nullable=False)
    lab_no = db.Column(db.Integer, db.ForeignKey('lab.lab_no'))

class Status(db.Model):
    equipment_id = db.Column(db.String(50), db.ForeignKey('equipment.equipment_id'))
    status_id = db.Column(db.String(50), primary_key=True)
    start_time = db.Column(db.DateTime)
    used_by = db.Column(db.String(255))

class Enrolled(db.Model):
    roll_no = db.Column(db.String(50), db.ForeignKey('student.roll_no'), primary_key=True)
    course_no = db.Column(db.String(50), db.ForeignKey('course.course_no'), primary_key=True)    


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        role = request.form['role']
        
        # Common validation
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return redirect(url_for('signup'))
        
        new_user = User(username=username, password=password, role=role)
        db.session.add(new_user)
        db.session.commit()
        
        if role == 'student':
            name = request.form['name']
            roll_no = request.form['roll_no']
            department = request.form['department']
            semester = request.form['semester']
            # Validation for roll_no
            if len(roll_no) != 9:
                flash('Student Roll number must be exactly 9 characters')
                return redirect(url_for('signup'))
            new_student = Student(user_id=new_user.id, name=name, roll_no=roll_no, department=department, semester=semester)
            db.session.add(new_student)
        elif role == 'research_student':
            name = request.form['name']
            roll_no = request.form['roll_no']
            department = request.form['department']
            # Validation for roll_no
            if not roll_no.startswith('r'):
                flash("Research Student Roll number must start with 'r'")
                return redirect(url_for('signup'))
            new_research_student = ResearchStudent(user_id=new_user.id, name=name, roll_no=roll_no, department=department)
            db.session.add(new_research_student)
        elif role in ['professor', 'lab_assistant']:
            faculty_name = request.form['faculty_name']
            faculty_id = request.form['faculty_id']
            course_no = request.form['course_no']
            department = request.form['department']
            new_faculty = Faculty(user_id=new_user.id, faculty_name=faculty_name, faculty_id=faculty_id, course_no=course_no, department=department)
            db.session.add(new_faculty)
        
        db.session.commit()
        flash('User created successfully')
        return redirect(url_for('login'))
    
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and user.password == password:
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html', user=current_user)

# Student view
@app.route('/view_labs')
@login_required
def view_labs():
    if current_user.role == 'student':
        labs = Lab.query.filter_by(lab_type='Academic').all()
    elif current_user.role in ['professor', 'lab_assistant']:
        labs = Lab.query.filter_by(lab_type='Academic').all()
    elif current_user.role == 'research_student':
        labs = Lab.query.all()
    else:
        return "Unauthorized", 403
    return render_template('view_labs.html', labs=labs)

# Professor view and update
@app.route('/manage_labs', methods=['GET', 'POST'])
@login_required
def manage_labs():
    if current_user.role != 'professor':
        return "Unauthorized", 403
    if request.method == 'POST':
        lab_no = request.form['lab_no']
        new_status = request.form['new_status']
        lab = Lab.query.filter_by(lab_no=lab_no).first()
        if lab:
            lab.is_available = new_status
            db.session.commit()
            flash('Lab status updated successfully')
        else:
            flash('Lab not found')
    labs = Lab.query.all()
    return render_template('manage_labs.html', labs=labs)

# Research student view and update equipment status
@app.route('/view_equipments', methods=['GET', 'POST'])
@login_required
def view_equipments():
    if current_user.role not in ['research_student', 'professor']:
        return "Unauthorized", 403

    if request.method == 'POST':
        equipment_id_to_remove = request.form.get('remove_equipment')
        if equipment_id_to_remove:
            # Check if the equipment is currently used by the current user
            existing_status = Status.query.filter_by(equipment_id=equipment_id_to_remove, used_by=current_user.username).first()
            if existing_status:
                try:
                    db.session.delete(existing_status)
                    db.session.commit()
                    flash('Equipment returned successfully', 'success')
                except Exception as e:
                    db.session.rollback()
                    flash('Failed to return equipment', 'error')

        equipment_id = request.form.get('equipment_id')
        if equipment_id:
            # Check if the equipment is already in use
            existing_status = Status.query.filter_by(equipment_id=equipment_id).first()
            if existing_status:
                # Equipment is in use, display the existing status record
                return render_template('equipment_status.html', status=existing_status)
            
            # Log the equipment usage
            used_by = current_user.username  # Assuming user's username is used for logging
            status_entry = Status(equipment_id=equipment_id, status_id=uuid.uuid4(), start_time=datetime.now(), used_by=used_by)
            try:
                db.session.add(status_entry)
                db.session.commit()
                flash('Equipment usage logged successfully', 'success')
            except Exception as e:
                db.session.rollback()
                flash('Failed to log equipment usage', 'error')

    equipments = Equipment.query.all()
    return render_template('view_equipments.html', equipments=equipments)


# Lab assistant manage academic labs
@app.route('/manage_academic_labs', methods=['GET', 'POST'])
@login_required
def manage_academic_labs():
    if current_user.role != 'lab_assistant':
        return "Unauthorized", 403
    if request.method == 'POST':
        lab_no = request.form['lab_no']
        new_status = request.form['new_status']
        lab = Lab.query.filter_by(lab_no=lab_no, lab_type='Academic').first()
        if lab:
            lab.is_available = new_status
            db.session.commit()
            flash('Lab status updated successfully')
        else:
            flash('Lab not found or not an Academic lab')
    labs = Lab.query.filter_by(lab_type='Academic').all()
    return render_template('manage_academic_labs.html', labs=labs)

# Add this route to display all entries from specified tables
@app.route('/statistics')
@login_required
def display_entries():
    if current_user.role not in ['professor', 'lab_assistant']:
        return "Unauthorized", 403
    
    projects = Project.query.all()
    funded_by = FundedBy.query.all()
    courses = Course.query.all()
    lab_courses = LabCourse.query.all()
    faculties = Faculty.query.all()

    return render_template('statistics.html', projects=projects, funded_by=funded_by, courses=courses, lab_courses=lab_courses, faculties=faculties)


if __name__ == '__main__':
    app.run(debug=True)
