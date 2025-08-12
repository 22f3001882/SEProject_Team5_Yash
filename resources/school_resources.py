from flask_restful import Api, Resource, fields, marshal_with
from flask_security import auth_required, current_user
from flask import request
from models import db, Class, Teacher, Parent, Child, User, School
from datetime import datetime

school_api = Api(prefix='/api/school')

# ------------------ Serialization Schemas ------------------

user_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'email': fields.String,
    'active': fields.Boolean,
}

class_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'teacher_id': fields.Integer,
    'school_id': fields.Integer,
}

# ------------------ Helpers ------------------

def is_school_admin():
    return any(role.name == 'admin' for role in current_user.roles)

# ------------------ Classes ------------------

class ClassList(Resource):
    @auth_required('token')
    @marshal_with(class_fields)
    def get(self):
        if not is_school_admin():
            return {'message': 'Not authorized'}, 403
        return Class.query.all()

    @auth_required('token')
    @marshal_with(class_fields)
    def post(self):
        if not is_school_admin():
            return {'message': 'Not authorized'}, 403

        data = request.get_json()
        name = data.get('name')
        teacher_id = data.get('teacher_id')
        school_id = data.get('school_id')

        if not all([name, teacher_id, school_id]):
            return {'message': 'Missing required fields'}, 400

        new_class = Class(name=name, teacher_id=teacher_id, school_id=school_id)
        db.session.add(new_class)
        db.session.commit()
        return new_class, 201

class ClassDetail(Resource):
    @auth_required('token')
    def delete(self, class_id):
        if not is_school_admin():
            return {'message': 'Not authorized'}, 403

        class_obj = Class.query.get(class_id)
        if not class_obj:
            return {'message': 'Class not found'}, 404

        db.session.delete(class_obj)
        db.session.commit()
        return {'message': 'Class deleted'}, 200

# ------------------ Teachers ------------------

class TeacherList(Resource):
    @auth_required('token')
    @marshal_with(user_fields)
    def get(self):
        if not is_school_admin():
            return {'message': 'Not authorized'}, 403

        teachers = Teacher.query.all()
        return [t.user_account for t in teachers]

    @auth_required('token')
    @marshal_with(user_fields)
    def post(self):
        if not is_school_admin():
            return {'message': 'Not authorized'}, 403

        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')
        school_id = data.get('school_id')

        if not all([name, email, password, school_id]):
            return {'message': 'Missing required fields'}, 400

        user = User(
            name=name,
            email=email,
            password=password,  # You should hash this!
            fs_uniquifier=email,
            active=True
        )
        db.session.add(user)
        db.session.flush()

        teacher = Teacher(user_id=user.id, school_id=school_id)
        db.session.add(teacher)
        db.session.commit()

        return user, 201

# ------------------ Parents ------------------

class ParentList(Resource):
    @auth_required('token')
    @marshal_with(user_fields)
    def get(self):
        if not is_school_admin():
            return {'message': 'Not authorized'}, 403

        parents = Parent.query.all()
        return [p.user_account for p in parents]

# ------------------ Children ------------------

class ChildList(Resource):
    @auth_required('token')
    @marshal_with(user_fields)
    def get(self):
        if not is_school_admin():
            return {'message': 'Not authorized'}, 403

        children = Child.query.all()
        return [c.user_account for c in children]

# ------------------ Register Resources ------------------

school_api.add_resource(ClassList, '/classes')
school_api.add_resource(ClassDetail, '/classes/<int:class_id>')

school_api.add_resource(TeacherList, '/teachers')
school_api.add_resource(ParentList, '/parents')
school_api.add_resource(ChildList, '/children')

def register_school_routes(app):
    school_api.init_app(app)