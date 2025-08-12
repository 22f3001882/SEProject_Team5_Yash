from flask import request, current_app as app
from flask_restful import Api, Resource, fields, marshal_with
from models import db, School, Teacher, Challenge, Class, User
from flask_security import auth_required

cache = app.cache
school_api = Api(prefix='/api/school')

# ========== Serialization Fields ==========

school_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'address': fields.String,
    'user_id': fields.Integer,
}
teacher_fields = {
    'id': fields.Integer,
    'user_id': fields.Integer,
    'school_id': fields.Integer,
    'name': fields.String,    # From User
    'email': fields.String,   # From User
}
challenge_fields = {
    'id': fields.Integer,
    'title': fields.String,
    'description': fields.String,
    'reward': fields.String,
    'created_on': fields.String,
    'ends_on': fields.String,
}
class_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'teacher_id': fields.Integer,
    'school_id': fields.Integer,
}
user_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'email': fields.String,
    'active': fields.Boolean,
}

# ========== School Identity ==========

class GetSchoolByIdApi(Resource):
    @auth_required('token')
    @marshal_with(school_fields)
    def get(self, school_id):
        return self.get_school_by_id(school_id)

    def get_school_by_id(self, school_id):
        school = School.query.get(school_id)
        if not school:
            return {'message': f'School with ID {school_id} not found'}, 404
        return school

class GetSchoolByUserIdApi(Resource):
    @auth_required('token')
    @marshal_with(school_fields)
    def get(self, user_id):
        return self.get_school_by_user_id(user_id)

    def get_school_by_user_id(self, user_id):
        school = School.query.filter_by(user_id=user_id).first()
        if not school:
            return {'message': 'School for this user not found'}, 404
        return school

# ========== Teacher Management ==========

class AddTeacherApi(Resource):
    @auth_required('token')
    @marshal_with(teacher_fields)
    def post(self, school_id):
        return self.add_teacher(school_id)

    def add_teacher(self, school_id):
        data = request.get_json()
        name = data.get("name")
        email = data.get("email")
        password = data.get("password")
        if not all([name, email, password]):
            return {'message': 'Missing required fields'}, 400
        # Create user
        from flask_security import hash_password
        user = User(name=name, email=email, password=hash_password(password), fs_uniquifier=email, active=True)
        db.session.add(user)
        db.session.flush()
        teacher = Teacher(user_id=user.id, school_id=school_id)
        db.session.add(teacher)
        db.session.commit()
        return {
            'id': teacher.id,
            'user_id': teacher.user_id,
            'school_id': teacher.school_id,
            'name': user.name,
            'email': user.email,
        }, 201

class DeleteTeacherApi(Resource):
    @auth_required('token')
    def delete(self, school_id, teacher_id):
        return self.delete_teacher(school_id, teacher_id)

    def delete_teacher(self, school_id, teacher_id):
        teacher = Teacher.query.filter_by(id=teacher_id, school_id=school_id).first()
        if not teacher:
            return {'message': 'Teacher not found for this school'}, 404
        db.session.delete(teacher)
        db.session.commit()
        return {'message': f'Teacher {teacher_id} removed from school {school_id}'}, 200

class GetAllTeachersApi(Resource):
    @auth_required('token')
    def get(self, school_id):
        return self.get_all_teachers(school_id)

    def get_all_teachers(self, school_id):
        teachers = Teacher.query.filter_by(school_id=school_id).all()
        result = []
        for t in teachers:
            if t.user_account:
                result.append({
                    'id': t.id,
                    'user_id': t.user_id,
                    'school_id': t.school_id,
                    'name': t.user_account.name,
                    'email': t.user_account.email,
                })
        return result

# ========== Challenge Management ==========

class CreateChallengeApi(Resource):
    @auth_required('token')
    @marshal_with(challenge_fields)
    def post(self, school_id):
        return self.create_challenge(school_id)

    def create_challenge(self, school_id):
        data = request.get_json()
        if not data or not data.get('title'):
            return {'message': 'Missing required fields'}, 400
        challenge = Challenge(
            title=data['title'],
            description=data.get('description'),
            reward=data.get('reward'),
            created_on=data.get('created_on'),
            ends_on=data.get('ends_on')
        )
        db.session.add(challenge)
        db.session.commit()
        return challenge, 201

class EditChallengeApi(Resource):
    @auth_required('token')
    @marshal_with(challenge_fields)
    def put(self, school_id, challenge_id):
        return self.edit_challenge(school_id, challenge_id)

    def edit_challenge(self, school_id, challenge_id):
        challenge = Challenge.query.get(challenge_id)
        if not challenge:
            return {'message': 'Challenge not found'}, 404
        data = request.get_json()
        if 'title' in data: challenge.title = data['title']
        if 'description' in data: challenge.description = data['description']
        if 'reward' in data: challenge.reward = data['reward']
        if 'ends_on' in data: challenge.ends_on = data['ends_on']
        db.session.commit()
        return challenge

class DeleteChallengeApi(Resource):
    @auth_required('token')
    def delete(self, school_id, challenge_id):
        return self.delete_challenge(school_id, challenge_id)

    def delete_challenge(self, school_id, challenge_id):
        challenge = Challenge.query.get(challenge_id)
        if not challenge:
            return {'message': 'Challenge not found'}, 404
        db.session.delete(challenge)
        db.session.commit()
        return {'message': f'Challenge {challenge_id} deleted'}, 200

# ========== Class and Reporting ==========

class GetAllClassesApi(Resource):
    @auth_required('token')
    @marshal_with(class_fields)
    def get(self, school_id):
        return self.get_all_classes(school_id)

    def get_all_classes(self, school_id):
        classes = Class.query.filter_by(school_id=school_id).all()
        return classes

class GetSchoolStatisticsApi(Resource):
    @auth_required('token')
    def get(self, school_id):
        return self.get_school_statistics(school_id)

    def get_school_statistics(self, school_id):
        num_classes = Class.query.filter_by(school_id=school_id).count()
        num_teachers = Teacher.query.filter_by(school_id=school_id).count()
        num_students = 0
        for c in Class.query.filter_by(school_id=school_id):
            num_students += len(c.students)
        return {
            'total_classes': num_classes,
            'total_teachers': num_teachers,
            'total_students': num_students
        }

class GenerateSchoolReportApi(Resource):
    @auth_required('token')
    def get(self, school_id):
        return self.generate_school_report(school_id)

    def generate_school_report(self, school_id):
        # Placeholder report
        stats = self.get_school_statistics(school_id)
        return {
            'report': f'Report for school {school_id}',
            'statistics': stats
        }

# ========== Register API routes ==========

school_api.add_resource(GetSchoolByIdApi, '/<int:school_id>')
school_api.add_resource(GetSchoolByUserIdApi, '/user/<int:user_id>')

school_api.add_resource(AddTeacherApi, '/<int:school_id>/teachers')
school_api.add_resource(DeleteTeacherApi, '/<int:school_id>/teachers/<int:teacher_id>')
school_api.add_resource(GetAllTeachersApi, '/<int:school_id>/teachers')

school_api.add_resource(CreateChallengeApi, '/<int:school_id>/challenges')
school_api.add_resource(EditChallengeApi, '/<int:school_id>/challenges/<int:challenge_id>')
school_api.add_resource(DeleteChallengeApi, '/<int:school_id>/challenges/<int:challenge_id>')

school_api.add_resource(GetAllClassesApi, '/<int:school_id>/classes')
school_api.add_resource(GetSchoolStatisticsApi, '/<int:school_id>/statistics')
school_api.add_resource(GenerateSchoolReportApi, '/<int:school_id>/report')

def register_school_routes(app):
    school_api.init_app(app)