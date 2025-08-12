from flask_restful import Api, Resource, fields, marshal_with
from flask_security import auth_required, current_user
from flask import request
from models import db, User, Role
from sqlalchemy.exc import IntegrityError

admin_api = Api(prefix='/api/admin')

# Serializers
user_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'email': fields.String,
    'active': fields.Boolean,
    'roles': fields.List(fields.String)
}

role_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'description': fields.String
}

# Helpers
def is_admin():
    return any(role.name == 'admin' for role in current_user.roles)

# ------------------ User Management ------------------

class AdminUserApi(Resource):
    @auth_required('token')
    @marshal_with(user_fields)
    def get(self):
        """List all users or filter by role"""
        if not is_admin():
            return {'message': 'Not authorized'}, 403

        role_filter = request.args.get('role')
        if role_filter:
            users = User.query.join(User.roles).filter(Role.name == role_filter).all()
        else:
            users = User.query.all()

        for user in users:
            user.roles = [r.name for r in user.roles]
        return users

    @auth_required('token')
    def delete(self, user_id):
        """Delete user"""
        if not is_admin():
            return {'message': 'Not authorized'}, 403

        user = User.query.get(user_id)
        if not user:
            return {'message': 'User not found'}, 404

        db.session.delete(user)
        db.session.commit()
        return {'message': f'User {user_id} deleted'}, 200

    @auth_required('token')
    def patch(self, user_id):
        """Activate or deactivate a user"""
        if not is_admin():
            return {'message': 'Not authorized'}, 403

        data = request.get_json()
        active_status = data.get('active')

        if active_status not in [True, False]:
            return {'message': 'Invalid active status'}, 400

        user = User.query.get(user_id)
        if not user:
            return {'message': 'User not found'}, 404

        user.active = active_status
        db.session.commit()
        return {'message': f"User {'activated' if active_status else 'deactivated'}"}, 200

    @auth_required('token')
    def put(self, user_id):
        """Update user roles"""
        if not is_admin():
            return {'message': 'Not authorized'}, 403

        data = request.get_json()
        roles_data = data.get('roles')  # List of role names

        if not roles_data:
            return {'message': 'Missing roles'}, 400

        user = User.query.get(user_id)
        if not user:
            return {'message': 'User not found'}, 404

        # Clear existing roles and assign new ones
        user.roles = []
        for role_name in roles_data:
            role = Role.query.filter_by(name=role_name).first()
            if role:
                user.roles.append(role)
            else:
                return {'message': f'Role not found: {role_name}'}, 400

        db.session.commit()
        return {'message': 'Roles updated successfully'}, 200

# ------------------ Role Management ------------------

class AdminRoleApi(Resource):
    @auth_required('token')
    @marshal_with(role_fields)
    def get(self):
        """List all roles"""
        if not is_admin():
            return {'message': 'Not authorized'}, 403

        return Role.query.all()

    @auth_required('token')
    @marshal_with(role_fields)
    def post(self):
        """Create a new role"""
        if not is_admin():
            return {'message': 'Not authorized'}, 403

        data = request.get_json()
        name = data.get('name')
        description = data.get('description')

        if not name or not description:
            return {'message': 'Missing required fields'}, 400

        role = Role(name=name, description=description)
        try:
            db.session.add(role)
            db.session.commit()
            return role, 201
        except IntegrityError:
            db.session.rollback()
            return {'message': 'Role already exists'}, 400

class AdminRoleDelete(Resource):
    @auth_required('token')
    def delete(self, role_id):
        """Delete a role"""
        if not is_admin():
            return {'message': 'Not authorized'}, 403

        role = Role.query.get(role_id)
        if not role:
            return {'message': 'Role not found'}, 404

        db.session.delete(role)
        db.session.commit()
        return {'message': 'Role deleted'}, 200

# ------------------ Route Registration ------------------

admin_api.add_resource(AdminUserApi, '/users', '/users/<int:user_id>')
admin_api.add_resource(AdminRoleApi, '/roles')
admin_api.add_resource(AdminRoleDelete, '/roles/<int:role_id>')

def register_admin_routes(app):
    admin_api.init_app(app)