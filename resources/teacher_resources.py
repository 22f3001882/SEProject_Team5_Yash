from flask import request, jsonify, current_app as app
from flask_restful import Api, Resource, fields, marshal_with
from models import db, Teacher, Class, Child, User
from flask_security import auth_required

cache = app.cache
teacher_api = Api(prefix='/api/teacher')

# -------- Serialization fields ---------
teacher_fields = {
    'id': fields.Integer,
    'user_id': fields.Integer,
    'school_id': fields.Integer,
}

user_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "email": fields.String,
    "active": fields.Boolean,
}

class_fields = {
    "id": fields.Integer,
    "name": fields.String,
    "teacher_id": fields.Integer,
    "school_id": fields.Integer,
}

student_fields = {
    "id": fields.Integer,
    "user_id": fields.Integer,
    "name": fields.String,
    "email": fields.String,
    "class_id": fields.Integer,
    "total_balance": fields.Float,
}

# ------------------ Teacher Identity ------------------ #

class GetTeacherByIdApi(Resource):
    @auth_required('token')
    @marshal_with(teacher_fields)
    def get(self, teacher_id):
        return self.get_teacher_by_id(teacher_id)

    def get_teacher_by_id(self, teacher_id):
        teacher = Teacher.query.get(teacher_id)
        if not teacher:
            return {'message': f'Teacher with ID {teacher_id} not found'}, 404
        return teacher

class GetTeacherByUserIdApi(Resource):
    @auth_required('token')
    @marshal_with(teacher_fields)
    def get(self, user_id):
        return self.get_teacher_by_user_id(user_id)

    def get_teacher_by_user_id(self, user_id):
        teacher = Teacher.query.filter_by(user_id=user_id).first()
        if not teacher:
            return {'message': f'Teacher for user_id {user_id} not found'}, 404
        return teacher

# ------------------ Class Management ------------------ #

class GetClassesApi(Resource):
    @auth_required('token')
    @marshal_with(class_fields)
    def get(self, teacher_id):
        return self.get_classes(teacher_id)

    def get_classes(self, teacher_id):
        classes = Class.query.filter_by(teacher_id=teacher_id).all()
        return classes

class AssignClassApi(Resource):
    @auth_required('token')
    def post(self, teacher_id, class_id):
        return self.assign_class(teacher_id, class_id)

    def assign_class(self, teacher_id, class_id):
        klass = Class.query.get(class_id)
        if not klass:
            return {'message': f'Class with ID {class_id} not found'}, 404
        klass.teacher_id = teacher_id
        db.session.commit()
        return {'message': f'Teacher {teacher_id} assigned to class {class_id}'}, 200

class CreateClassApi(Resource):
    @auth_required('token')
    @marshal_with(class_fields)
    def post(self, teacher_id):
        return self.create_class(teacher_id)

    def create_class(self, teacher_id):
        data = request.get_json()
        name = data.get('name')
        school_id = data.get('school_id')
        if not all([name, school_id]):
            return {'message': 'Missing required fields: name, school_id'}, 400
        new_class = Class(name=name, teacher_id=teacher_id, school_id=school_id)
        db.session.add(new_class)
        db.session.commit()
        return new_class, 201

class EditClassApi(Resource):
    @auth_required('token')
    @marshal_with(class_fields)
    def put(self, teacher_id, class_id):
        return self.edit_class(teacher_id, class_id)

    def edit_class(self, teacher_id, class_id):
        klass = Class.query.filter_by(id=class_id, teacher_id=teacher_id).first()
        if not klass:
            return {'message': 'Class not found for this teacher'}, 404
        data = request.get_json()
        if 'name' in data:
            klass.name = data['name']
        if 'school_id' in data:
            klass.school_id = data['school_id']
        db.session.commit()
        return klass

class DeleteClassApi(Resource):
    @auth_required('token')
    def delete(self, teacher_id, class_id):
        return self.delete_class(teacher_id, class_id)

    def delete_class(self, teacher_id, class_id):
        klass = Class.query.filter_by(id=class_id, teacher_id=teacher_id).first()
        if not klass:
            return {'message': 'Class not found for this teacher'}, 404
        db.session.delete(klass)
        db.session.commit()
        return {'message': f'Class {class_id} deleted for teacher {teacher_id}'}, 200

# ----------- Student Access -----------

class GetStudentsApi(Resource):
    @auth_required('token')
    @marshal_with(student_fields)
    def get(self, teacher_id):
        return self.get_students(teacher_id)

    def get_students(self, teacher_id):
        classes = Class.query.filter_by(teacher_id=teacher_id).all()
        students = []
        for klass in classes:
            # klass.students is a relationship
            for student in klass.students:
                # Append with required serializable fields
                students.append({
                    "id": student.id,
                    "user_id": student.user_id,
                    "name": student.user_account.name if student.user_account else "",
                    "email": student.user_account.email if student.user_account else "",
                    "class_id": student.class_id,
                    "total_balance": float(student.total_balance)
                })
        return students

# ----------- Educational Content -----------

class ShareEducationalContentApi(Resource):
    @auth_required('token')
    def post(self, teacher_id):
        return self.share_educational_content(teacher_id)

    def share_educational_content(self, teacher_id):
        # Assume 'content' field in POST data
        data = request.get_json()
        if not data or 'content' not in data:
            return {'message': 'Missing content'}, 400
        # You would save content to DB in real usage
        return {'message': f"Teacher {teacher_id} shared educational content"}, 201

# ---------- Register API routes ----------
teacher_api.add_resource(GetTeacherByIdApi, '/<int:teacher_id>')
teacher_api.add_resource(GetTeacherByUserIdApi, '/user/<int:user_id>')
teacher_api.add_resource(GetClassesApi, '/<int:teacher_id>/classes')
teacher_api.add_resource(AssignClassApi, '/<int:teacher_id>/classes/<int:class_id>/assign')
teacher_api.add_resource(CreateClassApi, '/<int:teacher_id>/classes')
teacher_api.add_resource(EditClassApi, '/<int:teacher_id>/classes/<int:class_id>')
teacher_api.add_resource(DeleteClassApi, '/<int:teacher_id>/classes/<int:class_id>')
teacher_api.add_resource(GetStudentsApi, '/<int:teacher_id>/students')
teacher_api.add_resource(ShareEducationalContentApi, '/<int:teacher_id>/content')

def register_teacher_routes(app):
    teacher_api.init_app(app)