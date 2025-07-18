from flask import jsonify, request, current_app as app
from flask_restful import Api, Resource, fields, marshal_with
from models import Goal, Child, User, db
from flask_security import auth_required, current_user
from datetime import datetime
from sqlalchemy.exc import IntegrityError

cache = app.cache
child_api = Api(prefix='/api/child')

# --------------------------Goal Fields-----------------------------

goal_fields = {
    'id': fields.Integer,
    'child_id': fields.Integer,
    'title': fields.String,
    'amount': fields.Float,
    'deadline': fields.String,
    'status': fields.String,
    'child_name': fields.String,
    'remaining_amount': fields.Float,
    'progress_percentage': fields.Float,
}

# --------------------------Goal Management-----------------------------

class GoalApi(Resource):
    @auth_required('token')
    @cache.memoize(timeout=5)
    @marshal_with(goal_fields)
    def get(self, goal_id):
        return self.fetch_goal_details(goal_id)
    
    @auth_required('token')
    @marshal_with(goal_fields)
    def put(self, goal_id):
        return self.update_goal_details(goal_id)
    
    @auth_required('token')
    def delete(self, goal_id):
        return self.remove_goal(goal_id)
    
    def fetch_goal_details(self, goal_id):
        """Fetch a specific goal with calculated fields"""
        goal = Goal.query.get(goal_id)
        if not goal:
            return {'message': 'Goal not found'}, 404
        
        # Check if user has permission to view this goal
        if not self._check_goal_access(goal):
            return {'message': 'Not authorized to view this goal'}, 403
        
        # Add calculated fields
        goal.child_name = goal.child.user_account.name if goal.child and goal.child.user_account else None
        goal.remaining_amount = float(goal.amount) - float(goal.child.total_balance) if goal.child else float(goal.amount)
        goal.progress_percentage = (float(goal.child.total_balance) / float(goal.amount)) * 100 if goal.amount > 0 and goal.child else 0
        
        return goal
    
    def update_goal_details(self, goal_id):
        """Update goal information"""
        goal = Goal.query.get(goal_id)
        if not goal:
            return {'message': 'Goal not found'}, 404
        
        # Check if user has permission to modify this goal
        if not self._check_goal_access(goal):
            return {'message': 'Not authorized to modify this goal'}, 403
        
        data = request.get_json()
        
        try:
            # Update allowed fields
            if 'title' in data:
                goal.title = data['title']
            if 'amount' in data:
                goal.amount = float(data['amount'])
            if 'deadline' in data:
                goal.deadline = datetime.strptime(data['deadline'], '%Y-%m-%d').date()
            if 'status' in data and data['status'] in ['active', 'completed', 'cancelled', 'waiting for approval']:
                goal.status = data['status']
            
            db.session.commit()
            
            # Add calculated fields for response
            goal.child_name = goal.child.user_account.name if goal.child and goal.child.user_account else None
            goal.remaining_amount = float(goal.amount) - float(goal.child.total_balance) if goal.child else float(goal.amount)
            goal.progress_percentage = (float(goal.child.total_balance) / float(goal.amount)) * 100 if goal.amount > 0 and goal.child else 0
            
            return goal, 200
            
        except ValueError as e:
            db.session.rollback()
            return {'message': f'Invalid data format: {str(e)}'}, 400
        except Exception as e:
            db.session.rollback()
            return {'message': f'Error updating goal: {str(e)}'}, 400
    
    def remove_goal(self, goal_id):
        """Delete a goal"""
        goal = Goal.query.get(goal_id)
        if not goal:
            return {'message': 'Goal not found'}, 404
        
        # Check if user has permission to delete this goal
        if not self._check_goal_access(goal):
            return {'message': 'Not authorized to delete this goal'}, 403
        
        try:
            db.session.delete(goal)
            db.session.commit()
            return {'message': 'Goal deleted successfully'}, 200
        except Exception as e:
            db.session.rollback()
            return {'message': f'Error deleting goal: {str(e)}'}, 400
    
    def _check_goal_access(self, goal):
        """Check if current user has access to this goal"""
        if 'admin' in current_user.roles:
            return True
        
        # If user is a child, they can only access their own goals
        if 'child' in current_user.roles:
            child = Child.query.filter_by(user_id=current_user.id).first()
            return child and child.id == goal.child_id
        
        # If user is a parent, they can access their child's goals
        if 'parent' in current_user.roles:
            # This would need parent-child relationship logic
            # For now, allowing parents to view any child's goals
            return True
        
        return False


class GoalListApi(Resource):
    @auth_required('token')
    @cache.cached(timeout=5)
    @marshal_with(goal_fields)
    def get(self):
        return self.fetch_all_goals()
    
    @auth_required('token')
    @marshal_with(goal_fields)
    def post(self):
        return self.create_new_goal()
    
    def fetch_all_goals(self):
        """Fetch all goals accessible to current user"""
        # Filter goals based on user role
        if 'admin' in current_user.roles:
            goals = Goal.query.all()
        elif 'child' in current_user.roles:
            child = Child.query.filter_by(user_id=current_user.id).first()
            goals = Goal.query.filter_by(child_id=child.id).all() if child else []
        elif 'parent' in current_user.roles:
            # For parents, show all their children's goals
            # This would need proper parent-child relationship logic
            goals = Goal.query.all()  # Simplified for now
        else:
            goals = []
        
        # Add calculated fields to each goal
        for goal in goals:
            goal.child_name = goal.child.user_account.name if goal.child and goal.child.user_account else None
            goal.remaining_amount = float(goal.amount) - float(goal.child.total_balance) if goal.child else float(goal.amount)
            goal.progress_percentage = (float(goal.child.total_balance) / float(goal.amount)) * 100 if goal.amount > 0 and goal.child else 0
        
        return goals
    
    def create_new_goal(self):
        """Create a new goal"""
        data = request.get_json()
        
        if not data:
            return {'message': 'No data provided'}, 400
        
        # Validate required fields
        required_fields = ['title', 'amount']
        for field in required_fields:
            if field not in data:
                return {'message': f'Missing required field: {field}'}, 400
        
        try:
            # Determine child_id based on user role
            child_id = None
            if 'child' in current_user.roles:
                child = Child.query.filter_by(user_id=current_user.id).first()
                if not child:
                    return {'message': 'Child profile not found'}, 404
                child_id = child.id
            elif 'parent' in current_user.roles or 'admin' in current_user.roles:
                # Parent or admin can specify child_id
                child_id = data.get('child_id')
                if not child_id:
                    return {'message': 'child_id is required for parent/admin'}, 400
            else:
                return {'message': 'Not authorized to create goals'}, 403
            
            # Validate child exists
            child = Child.query.get(child_id)
            if not child:
                return {'message': 'Child not found'}, 404
            
            # Parse deadline if provided
            deadline = None
            if 'deadline' in data and data['deadline']:
                deadline = datetime.strptime(data['deadline'], '%Y-%m-%d').date()
            
            # Create goal
            goal = Goal(
                child_id=child_id,
                title=data['title'],
                amount=float(data['amount']),
                deadline=deadline,
                status=data.get('status', 'active')
            )
            
            db.session.add(goal)
            db.session.commit()
            
            # Add calculated fields for response
            goal.child_name = goal.child.user_account.name if goal.child and goal.child.user_account else None
            goal.remaining_amount = float(goal.amount) - float(goal.child.total_balance) if goal.child else float(goal.amount)
            goal.progress_percentage = (float(goal.child.total_balance) / float(goal.amount)) * 100 if goal.amount > 0 and goal.child else 0
            
            return goal, 201
            
        except ValueError as e:
            db.session.rollback()
            return {'message': f'Invalid data format: {str(e)}'}, 400
        except IntegrityError as e:
            db.session.rollback()
            return {'message': 'Database integrity error'}, 400
        except Exception as e:
            db.session.rollback()
            return {'message': f'Error creating goal: {str(e)}'}, 400


class ChildGoalsApi(Resource):
    @auth_required('token')
    @cache.cached(timeout=5)
    @marshal_with(goal_fields)
    def get(self, child_id):
        return self.fetch_child_goals(child_id)
    
    def fetch_child_goals(self, child_id):
        """Fetch all goals for a specific child"""
        child = Child.query.get(child_id)
        if not child:
            return {'message': 'Child not found'}, 404
        
        # Check access permissions
        if not self._check_child_access(child):
            return {'message': 'Not authorized to view this child\'s goals'}, 403
        
        goals = Goal.query.filter_by(child_id=child_id).all()
        
        # Add calculated fields
        for goal in goals:
            goal.child_name = child.user_account.name if child.user_account else None
            goal.remaining_amount = float(goal.amount) - float(child.total_balance)
            goal.progress_percentage = (float(child.total_balance) / float(goal.amount)) * 100 if goal.amount > 0 else 0
        
        return goals
    
    def _check_child_access(self, child):
        """Check if current user has access to this child"""
        if 'admin' in current_user.roles:
            return True
        
        # If user is the child themselves
        if 'child' in current_user.roles:
            return child.user_id == current_user.id
        
        # If user is a parent (would need parent-child relationship logic)
        if 'parent' in current_user.roles:
            return True  # Simplified for now
        
        return False


# Register API routes
child_api.add_resource(GoalApi, '/goals/<int:goal_id>')
child_api.add_resource(GoalListApi, '/goals')
child_api.add_resource(ChildGoalsApi, '/children/<int:child_id>/goals')





def register_child_routes(app):
    child_api.init_app(app)

