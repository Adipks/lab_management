from app import app, db
from app import User, Lab, Equipment,Student,ResearchStudent,Faculty,Status,Enrolled,Course,LabCourse,Project,FundedBy # Import your models

with app.app_context():
    db.create_all()