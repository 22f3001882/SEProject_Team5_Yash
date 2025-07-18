from flask import current_app as app
from models import db, Goal, Child
from flask_security import SQLAlchemySessionUserDatastore, hash_password
from datetime import datetime

with app.app_context():
    db.create_all()
    userdatastore : SQLAlchemySessionUserDatastore = app.security.datastore
    userdatastore.find_or_create_role(name='admin', description='admin')
    userdatastore.find_or_create_role(name='child', description='children')
    userdatastore.find_or_create_role(name='parent', description='parents')
    userdatastore.find_or_create_role(name='school', description='schools')
    userdatastore.find_or_create_role(name='teacher', description='teachers')

    if not (userdatastore.find_user(email='admin@kidsche.com')):
        userdatastore.create_user(email= 'admin@kidsche.com', password=hash_password('pass'), roles = ['admin'], name='Admin')
    if not (userdatastore.find_user(email='user@kidsche.com')):
        userdatastore.create_user(email= 'user@kidsche.com', password=hash_password('pass'), roles = ['child'], name='Child')
    if not Goal.query.first():
        default_goal = Goal(child_id = '1', title = 'Default', amount = '500', deadline = datetime.strptime("01-01-2025", "%d-%m-%Y"), status = 'completed')
        db.session.add(default_goal)
    # if not Chapter.query.first():
    #     default_chapter = Chapter(subject_id=1, name='Default', description="This is a default chapter.")
    #     db.session.add(default_chapter)
    # if not Quiz.query.first():
    #     default_quiz = Quiz(chapter_id=1, remarks="This is a default quiz.",creation_date=datetime.strptime("01-01-2025", "%d-%m-%Y"), date_of_quiz = datetime.strptime("01-01-2025", "%d-%m-%Y"), time_duration= "00:00")
    #     db.session.add(default_quiz)
    db.session.commit()

