from flask_restful import Api, Resource, fields, marshal_with
from flask_security import auth_required, current_user
from flask import request
from models import db, Teacher, Class, Child, Challenge, ChallengeProgress, NotesEncouragement
from datetime import datetime

teacher_api = Api(prefix="/api/teacher")

class_fields = {
    'id': fields.Integer,
    'name': fields.String
}

student_fields = {
    'id': fields.Integer,
    'name': fields.String
}

tip_fields = {
    'id': fields.Integer,
    'title': fields.String,
    'description': fields.String
}

# Resources

class TeacherClassList(Resource):
    @auth_required('token')
    @marshal_with(class_fields)
    def get(self):
        """Get all classes for current teacher"""
        teacher = Teacher.query.filter_by(user_id=current_user.id).first()
        return teacher.classes if teacher else []

class TeacherStudentList(Resource):
    @auth_required('token')
    @marshal_with(student_fields)
    def get(self, class_id):
        """Get all students in a class"""
        children = Child.query.filter_by(class_id=class_id).all()
        for child in children:
            child.name = child.user_account.name
        return children

class TeacherSendTip(Resource):
    @auth_required('token')
    def post(self, child_id):
        """Send a tip to a child"""
        data = request.get_json()
        if not data or 'message' not in data:
            return {'message': 'Tip message is required'}, 400
        tip = NotesEncouragement(
            sender_id=current_user.id,
            child_id=child_id,
            message=data['message'],
            date_sent=datetime.utcnow()
        )
        db.session.add(tip)
        db.session.commit()
        return {'message': 'Tip sent successfully'}, 201

# Register endpoints
teacher_api.add_resource(TeacherClassList, '/classroom/overview')
teacher_api.add_resource(TeacherStudentList, '/students/<int:class_id>')
teacher_api.add_resource(TeacherSendTip, '/students/<int:child_id>/tip')

def register_teacher_routes(app):
    teacher_api.init_app(app)