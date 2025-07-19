from flask import jsonify, request, current_app as app
from flask_restful import Api, Resource, fields, marshal_with
from models import Goal, Child, User, db
from flask_security import auth_required, current_user
from datetime import datetime
from sqlalchemy.exc import IntegrityError
from models import PocketMoneyPlace, PocketMoneyLog, Challenge, ChallengeProgress, Spending
from sqlalchemy import func, desc

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


# --------------------------Spending Fields-----------------------------
spending_fields = {
    'id': fields.Integer,
    'child_id': fields.Integer,
    'category': fields.String,
    'amount': fields.Float,
    'spend_date': fields.String,
    'description': fields.String,
    'child_name': fields.String,
}

# --------------------------Spending Management-----------------------------
class SpendingApi(Resource):
    @auth_required('token')
    @cache.memoize(timeout=5)
    @marshal_with(spending_fields)
    def get(self, spend_id):
        return self.fetch_spending_details(spend_id)

    @auth_required('token')
    @marshal_with(spending_fields)
    def put(self, spend_id):
        return self.update_spending_details(spend_id)

    @auth_required('token')
    def delete(self, spend_id):
        return self.remove_spending(spend_id)

    def fetch_spending_details(self, spend_id):
        """Fetch a specific spending record"""
        if 'child' in current_user.roles:
            child = Child.query.filter_by(user_id=current_user.id).first()
            if not child:
                return {'message': 'Child not found'}, 404
        else:
            return {'message': 'Not authorized'}, 403

        spend = Spending.query.filter_by(id=spend_id, child_id=child.id).first()
        if not spend:
            return {'message': 'Spending record not found'}, 404

        # Add calculated fields
        spend.child_name = child.user_account.name if child.user_account else None
        return spend

    def update_spending_details(self, spend_id):
        """Update spending record following child_routes.py pattern"""
        if 'child' in current_user.roles:
            child = Child.query.filter_by(user_id=current_user.id).first()
            if not child:
                return {'message': 'Child not found'}, 404
        else:
            return {'message': 'Not authorized'}, 403

        spend = Spending.query.filter_by(id=spend_id, child_id=child.id).first()
        if not spend:
            return {'message': 'Spending record not found'}, 404

        data = request.get_json()
        if not data:
            return {'message': 'No data provided'}, 400

        try:
            old_amount = float(spend.amount)
            
            if 'category' in data:
                spend.category = data['category']
            if 'amount' in data:
                new_amount = float(data['amount'])
                # Adjust balance based on amount change
                balance_change = old_amount - new_amount
                child.total_balance += balance_change
                spend.amount = new_amount
            if 'spend_date' in data:
                spend.spend_date = datetime.strptime(data['spend_date'], '%Y-%m-%d').date()
            if 'description' in data:
                spend.description = data['description']

            db.session.commit()
            
            spend.child_name = child.user_account.name if child.user_account else None
            return spend, 200

        except Exception as e:
            db.session.rollback()
            return {'message': f'Error updating spending record: {str(e)}'}, 400

    def remove_spending(self, spend_id):
        """Delete spending record and restore balance"""
        if 'child' in current_user.roles:
            child = Child.query.filter_by(user_id=current_user.id).first()
            if not child:
                return {'message': 'Child not found'}, 404
        else:
            return {'message': 'Not authorized'}, 403

        spend = Spending.query.filter_by(id=spend_id, child_id=child.id).first()
        if not spend:
            return {'message': 'Spending record not found'}, 404

        try:
            # Restore balance
            child.total_balance += float(spend.amount)
            db.session.delete(spend)
            db.session.commit()
            
            return {'message': 'Spending record deleted successfully', 'new_balance': float(child.total_balance)}, 200
        except Exception as e:
            db.session.rollback()
            return {'message': f'Error deleting spending record: {str(e)}'}, 400

class SpendingListApi(Resource):
    @auth_required('token')
    @cache.cached(timeout=5)
    @marshal_with(spending_fields)
    def get(self):
        return self.fetch_all_spendings()

    @auth_required('token')
    @marshal_with(spending_fields)
    def post(self):
        return self.create_new_spending()

    def fetch_all_spendings(self):
        """Fetch spending records with filtering options like child_routes.py"""
        if 'child' in current_user.roles:
            child = Child.query.filter_by(user_id=current_user.id).first()
            if not child:
                return {'message': 'Child not found'}, 404
        else:
            return {'message': 'Not authorized'}, 403

        # Get query parameters for filtering (matching child_routes.py)
        category = request.args.get('category')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', 50, type=int)

        query = Spending.query.filter_by(child_id=child.id)

        if category:
            query = query.filter(Spending.category == category)
        if start_date:
            query = query.filter(Spending.spend_date >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(Spending.spend_date <= datetime.strptime(end_date, '%Y-%m-%d').date())

        spendings = query.order_by(Spending.spend_date.desc()).limit(limit).all()

        for spending in spendings:
            spending.child_name = child.user_account.name if child.user_account else None

        return spendings

    def create_new_spending(self):
        """Create spending record with balance validation"""
        if 'child' in current_user.roles:
            child = Child.query.filter_by(user_id=current_user.id).first()
            if not child:
                return {'message': 'Child not found'}, 404
        else:
            return {'message': 'Not authorized'}, 403

        data = request.get_json()
        if not data:
            return {'message': 'No data provided'}, 400

        required_fields = ['category', 'amount', 'spend_date']
        for field in required_fields:
            if field not in data:
                return {'message': f'Missing required field: {field}'}, 400

        # Check if child has enough balance
        if float(data['amount']) > float(child.total_balance):
            return {'message': 'Insufficient balance'}, 400

        try:
            spending = Spending(
                child_id=child.id,
                category=data['category'],
                amount=data['amount'],
                spend_date=datetime.strptime(data['spend_date'], '%Y-%m-%d').date(),
                description=data.get('description', '')
            )

            # Update child's balance
            child.total_balance -= float(data['amount'])

            db.session.add(spending)
            db.session.commit()

            spending.child_name = child.user_account.name if child.user_account else None
            return spending, 201

        except Exception as e:
            db.session.rollback()
            return {'message': f'Error creating spending record: {str(e)}'}, 400

# --------------------------Money Sources Fields-----------------------------
money_source_fields = {
    'id': fields.Integer,
    'child_id': fields.Integer,
    'name': fields.String,
    'amount_stored': fields.Float,
    'child_name': fields.String,
}

class MoneySourceApi(Resource):
    @auth_required('token')
    @cache.memoize(timeout=5)
    @marshal_with(money_source_fields)
    def get(self, source_id):
        return self.fetch_money_source_details(source_id)

    @auth_required('token')
    @marshal_with(money_source_fields)
    def put(self, source_id):
        return self.update_money_source_details(source_id)

    @auth_required('token')
    def delete(self, source_id):
        return self.remove_money_source(source_id)

    def fetch_money_source_details(self, source_id):
        """Fetch specific money source"""
        if 'child' in current_user.roles:
            child = Child.query.filter_by(user_id=current_user.id).first()
            if not child:
                return {'message': 'Child not found'}, 404
        else:
            return {'message': 'Not authorized'}, 403

        place = PocketMoneyPlace.query.filter_by(id=source_id, child_id=child.id).first()
        if not place:
            return {'message': 'Money source not found'}, 404

        place.child_name = child.user_account.name if child.user_account else None
        return place

    def update_money_source_details(self, source_id):
        """Update money source following child_routes.py pattern"""
        if 'child' in current_user.roles:
            child = Child.query.filter_by(user_id=current_user.id).first()
            if not child:
                return {'message': 'Child not found'}, 404
        else:
            return {'message': 'Not authorized'}, 403

        place = PocketMoneyPlace.query.filter_by(id=source_id, child_id=child.id).first()
        if not place:
            return {'message': 'Money source not found'}, 404

        data = request.get_json()
        if not data:
            return {'message': 'No data provided'}, 400

        try:
            if 'name' in data:
                place.name = data['name']
            if 'amount_stored' in data:
                place.amount_stored = data['amount_stored']

            db.session.commit()
            
            place.child_name = child.user_account.name if child.user_account else None
            return place, 200

        except Exception as e:
            db.session.rollback()
            return {'message': f'Error updating money source: {str(e)}'}, 400

    def remove_money_source(self, source_id):
        """Delete money source"""
        if 'child' in current_user.roles:
            child = Child.query.filter_by(user_id=current_user.id).first()
            if not child:
                return {'message': 'Child not found'}, 404
        else:
            return {'message': 'Not authorized'}, 403

        place = PocketMoneyPlace.query.filter_by(id=source_id, child_id=child.id).first()
        if not place:
            return {'message': 'Money source not found'}, 404

        try:
            db.session.delete(place)
            db.session.commit()
            return {'message': 'Money source deleted successfully'}, 200
        except Exception as e:
            db.session.rollback()
            return {'message': f'Error deleting money source: {str(e)}'}, 400

class MoneySourceListApi(Resource):
    @auth_required('token')
    @cache.cached(timeout=5)
    @marshal_with(money_source_fields)
    def get(self):
        return self.fetch_all_money_sources()

    @auth_required('token')
    @marshal_with(money_source_fields)
    def post(self):
        return self.create_new_money_source()

    def fetch_all_money_sources(self):
        """Fetch all money storage places"""
        if 'child' in current_user.roles:
            child = Child.query.filter_by(user_id=current_user.id).first()
            if not child:
                return {'message': 'Child not found'}, 404
        else:
            return {'message': 'Not authorized'}, 403

        places = PocketMoneyPlace.query.filter_by(child_id=child.id).all()

        for place in places:
            place.child_name = child.user_account.name if child.user_account else None

        return places

    def create_new_money_source(self):
        """Create new money storage place"""
        if 'child' in current_user.roles:
            child = Child.query.filter_by(user_id=current_user.id).first()
            if not child:
                return {'message': 'Child not found'}, 404
        else:
            return {'message': 'Not authorized'}, 403

        data = request.get_json()
        if not data:
            return {'message': 'No data provided'}, 400

        if 'name' not in data:
            return {'message': 'Missing required field: name'}, 400

        try:
            place = PocketMoneyPlace(
                child_id=child.id,
                name=data['name'],
                amount_stored=data.get('amount_stored', 0.00)
            )

            db.session.add(place)
            db.session.commit()

            place.child_name = child.user_account.name if child.user_account else None
            return place, 201

        except Exception as e:
            db.session.rollback()
            return {'message': f'Error creating money source: {str(e)}'}, 400


# --------------------------Balance Fields-----------------------------
balance_fields = {
    'total_balance': fields.Float,
    'places_breakdown': fields.List(fields.Raw),
    'recent_transactions': fields.List(fields.Raw),
}

class BalanceApi(Resource):
    @auth_required('token')
    @cache.cached(timeout=5)
    @marshal_with(balance_fields)
    def get(self):
        return self.fetch_balance_details()

    def fetch_balance_details(self):
        """Get child's balance breakdown like child_routes.py"""
        if 'child' in current_user.roles:
            child = Child.query.filter_by(user_id=current_user.id).first()
            if not child:
                return {'message': 'Child not found'}, 404
        else:
            return {'message': 'Not authorized'}, 403

        # Get money places breakdown
        places = PocketMoneyPlace.query.filter_by(child_id=child.id).all()
        places_breakdown = []
        for place in places:
            places_breakdown.append({
                'name': place.name,
                'amount': float(place.amount_stored)
            })

        # Get recent transactions
        recent_logs = PocketMoneyLog.query.filter_by(child_id=child.id).order_by(
            PocketMoneyLog.date.desc()
        ).limit(5).all()
        
        recent_transactions = []
        for log in recent_logs:
            recent_transactions.append({
                'amount': float(log.amount),
                'date': log.date.isoformat(),
                'source': log.source,
                'destination': log.destination
            })

        return {
            'total_balance': float(child.total_balance),
            'places_breakdown': places_breakdown,
            'recent_transactions': recent_transactions
        }

# --------------------------Challenge Progress Fields-----------------------------
challenge_progress_fields = {
    'challenge_id': fields.Integer,
    'child_id': fields.Integer,
    'title': fields.String,
    'description': fields.String,
    'reward': fields.String,
    'status': fields.String,
    'ends_on': fields.String,
    'has_started': fields.Boolean,
}

class CurrentChallengesApi(Resource):
    @auth_required('token')
    @cache.cached(timeout=5)
    @marshal_with(challenge_progress_fields)
    def get(self):
        return self.fetch_current_challenges()

    def fetch_current_challenges(self):
        """Get current active challenges like child_routes.py"""
        if 'child' in current_user.roles:
            child = Child.query.filter_by(user_id=current_user.id).first()
            if not child:
                return {'message': 'Child not found'}, 404
        else:
            return {'message': 'Not authorized'}, 403

        # Get challenges that haven't ended yet
        current_challenges = Challenge.query.filter(
            Challenge.ends_on > datetime.now()
        ).all()

        challenges_data = []
        for challenge in current_challenges:
            # Check if child has progress on this challenge
            progress = ChallengeProgress.query.filter_by(
                child_id=child.id,
                challenge_id=challenge.id
            ).first()

            challenge_info = {
                'challenge_id': challenge.id,
                'child_id': child.id,
                'title': challenge.title,
                'description': challenge.description,
                'reward': challenge.reward,
                'ends_on': challenge.ends_on.isoformat(),
                'status': progress.status if progress else 'available',
                'has_started': progress is not None
            }
            challenges_data.append(challenge_info)

        return challenges_data

class ChallengeCompletionApi(Resource):
    @auth_required('token')
    def post(self, challenge_id):
        return self.complete_challenge(challenge_id)

    def complete_challenge(self, challenge_id):
        """Mark challenge as completed following child_routes.py pattern"""
        if 'child' in current_user.roles:
            child = Child.query.filter_by(user_id=current_user.id).first()
            if not child:
                return {'message': 'Child not found'}, 404
        else:
            return {'message': 'Not authorized'}, 403

        challenge = Challenge.query.get(challenge_id)
        if not challenge:
            return {'message': 'Challenge not found'}, 404

        # Check if challenge is still active
        if challenge.ends_on and challenge.ends_on < datetime.now():
            return {'message': 'Challenge has expired'}, 400

        # Get or create progress record
        progress = ChallengeProgress.query.filter_by(
            child_id=child.id,
            challenge_id=challenge_id
        ).first()

        if not progress:
            progress = ChallengeProgress(
                child_id=child.id,
                challenge_id=challenge_id,
                status='started'
            )
            db.session.add(progress)

        try:
            progress.status = 'completed'
            db.session.commit()

            return {
                'message': 'Challenge completed successfully',
                'challenge_id': challenge_id,
                'status': 'completed',
                'reward': challenge.reward
            }, 200

        except Exception as e:
            db.session.rollback()
            return {'message': f'Error completing challenge: {str(e)}'}, 400


# Register API routes matching child_routes.py patterns
child_api.add_resource(SpendingApi, '/spends/<int:spend_id>')
child_api.add_resource(SpendingListApi, '/spends')
child_api.add_resource(MoneySourceApi, '/money-sources/<int:source_id>')
child_api.add_resource(MoneySourceListApi, '/money-sources')
child_api.add_resource(BalanceApi, '/balance')
child_api.add_resource(CurrentChallengesApi, '/challenges/current')
child_api.add_resource(ChallengeCompletionApi, '/challenges/<int:challenge_id>/complete')


def register_child_routes(app):
    child_api.init_app(app)

