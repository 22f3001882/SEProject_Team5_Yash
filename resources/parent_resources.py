from flask import jsonify, request, current_app as app
from flask_restful import Api, Resource, fields, marshal_with
from models import (
    Child, Parent, User, Goal, Spending, PocketMoney, PocketMoneyPlace, 
    PocketMoneyLog, Challenge, ChallengeProgress, NotesEncouragement, 
    ParentChildLink, db
)
from flask_security import auth_required, current_user
from datetime import datetime, date, timedelta
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, desc

cache = app.cache
parent_api = Api(prefix='/api/parent')

# --------------------------Child Fields-----------------------------
child_fields = {
    'id': fields.Integer,
    'user_id': fields.Integer,
    'name': fields.String,
    'email': fields.String,
    'total_balance': fields.Float,
    'class_name': fields.String,
    'goals_count': fields.Integer,
    'recent_activity': fields.List(fields.Raw),
}

# --------------------------Child Overview Fields-----------------------------
child_overview_fields = {
    'id': fields.Integer,
    'name': fields.String,
    'total_balance': fields.Float,
    'goals': fields.List(fields.Raw),
    'recent_spending': fields.List(fields.Raw),
    'money_sources': fields.List(fields.Raw),
    'spending_summary': fields.Raw,
    'achievement_progress': fields.Raw,
}

# --------------------------Allowance Fields-----------------------------
allowance_fields = {
    'id': fields.Integer,
    'child_id': fields.Integer,
    'child_name': fields.String,
    'amount': fields.Float,
    'date_given': fields.String,
    'recurring': fields.Boolean,
    'recurring_schedule': fields.String,
    'stored_in': fields.String,
}

# --------------------------Report Fields-----------------------------
report_fields = {
    'summary': fields.Raw,
    'children_data': fields.List(fields.Raw),
    'spending_trends': fields.List(fields.Raw),
    'transactions': fields.List(fields.Raw),
    'generated_at': fields.String,
}

# --------------------------Message Fields-----------------------------
message_fields = {
    'id': fields.Integer,
    'sender_id': fields.Integer,
    'child_id': fields.Integer,
    'sender_name': fields.String,
    'child_name': fields.String,
    'message': fields.String,
    'date_sent': fields.String,
}

# --------------------------Children Management-----------------------------
class ChildrenApi(Resource):
    @auth_required('token')
    @cache.cached(timeout=5)
    @marshal_with(child_fields)
    def get(self):
        return self.fetch_all_children()

    @auth_required('token')
    @marshal_with(child_fields)
    def post(self):
        return self.create_new_child()

    def fetch_all_children(self):
        """Get all children linked to the current parent"""
        if 'parent' not in current_user.roles:
            return {'message': 'Not authorized'}, 403

        parent = Parent.query.filter_by(user_id=current_user.id).first()
        if not parent:
            return {'message': 'Parent profile not found'}, 404

        # Get all children linked to this parent
        children_links = ParentChildLink.query.filter_by(parent_id=parent.id).all()
        children_data = []

        for link in children_links:
            child = link.child
            if child and child.user_account:
                # Get recent activity
                recent_spending = Spending.query.filter_by(child_id=child.id).order_by(
                    desc(Spending.spend_date)
                ).limit(3).all()
                
                recent_activity = []
                for spend in recent_spending:
                    recent_activity.append({
                        'type': 'spending',
                        'amount': float(spend.amount),
                        'category': spend.category,
                        'date': spend.spend_date.isoformat()
                    })

                child_data = {
                    'id': child.id,
                    'user_id': child.user_id,
                    'name': child.user_account.name,
                    'email': child.user_account.email,
                    'total_balance': float(child.total_balance),
                    'class_name': child.class_info.name if child.class_info else None,
                    'goals_count': Goal.query.filter_by(child_id=child.id).count(),
                    'recent_activity': recent_activity
                }
                children_data.append(child_data)

        return children_data

    def create_new_child(self):
        """Create a new child profile and link to parent"""
        if 'parent' not in current_user.roles:
            return {'message': 'Not authorized'}, 403

        parent = Parent.query.filter_by(user_id=current_user.id).first()
        if not parent:
            return {'message': 'Parent profile not found'}, 404

        data = request.get_json()
        if not data:
            return {'message': 'No data provided'}, 400

        required_fields = ['name', 'email', 'class_id']
        for field in required_fields:
            if field not in data:
                return {'message': f'Missing required field: {field}'}, 400

        try:
            # Check if user already exists
            existing_user = User.query.filter_by(email=data['email']).first()
            if existing_user:
                return {'message': 'User with this email already exists'}, 400

            # Create user account
            from flask_security import hash_password
            user = User(
                email=data['email'],
                password=hash_password('defaultpassword123'),  # Parent should change this
                name=data['name'],
                fs_uniquifier=f"child_{data['email']}_{datetime.now().timestamp()}",
                active=True
            )
            db.session.add(user)
            db.session.flush()

            # Create child profile
            child = Child(
                user_id=user.id,
                class_id=data['class_id'],
                total_balance=data.get('initial_balance', 0.00)
            )
            db.session.add(child)
            db.session.flush()

            # Link child to parent
            link = ParentChildLink(
                parent_id=parent.id,
                child_id=child.id,
                primary=True
            )
            db.session.add(link)
            db.session.commit()

            return {
                'id': child.id,
                'user_id': user.id,
                'name': user.name,
                'email': user.email,
                'total_balance': float(child.total_balance),
                'class_name': child.class_info.name if child.class_info else None,
                'goals_count': 0,
                'recent_activity': []
            }, 201

        except Exception as e:
            db.session.rollback()
            return {'message': f'Error creating child: {str(e)}'}, 400

class ChildApi(Resource):
    @auth_required('token')
    @cache.memoize(timeout=5)
    @marshal_with(child_fields)
    def get(self, child_id):
        return self.fetch_child_details(child_id)

    @auth_required('token')
    @marshal_with(child_fields)
    def put(self, child_id):
        return self.update_child_details(child_id)

    @auth_required('token')
    def delete(self, child_id):
        return self.remove_child(child_id)

    def fetch_child_details(self, child_id):
        """Get specific child details"""
        if not self._check_child_access(child_id):
            return {'message': 'Not authorized to view this child'}, 403

        child = Child.query.get(child_id)
        if not child:
            return {'message': 'Child not found'}, 404

        # Get recent activity
        recent_spending = Spending.query.filter_by(child_id=child.id).order_by(
            desc(Spending.spend_date)
        ).limit(5).all()
        
        recent_activity = []
        for spend in recent_spending:
            recent_activity.append({
                'type': 'spending',
                'amount': float(spend.amount),
                'category': spend.category,
                'date': spend.spend_date.isoformat()
            })

        return {
            'id': child.id,
            'user_id': child.user_id,
            'name': child.user_account.name if child.user_account else None,
            'email': child.user_account.email if child.user_account else None,
            'total_balance': float(child.total_balance),
            'class_name': child.class_info.name if child.class_info else None,
            'goals_count': Goal.query.filter_by(child_id=child.id).count(),
            'recent_activity': recent_activity
        }

    def update_child_details(self, child_id):
        """Update child information"""
        if not self._check_child_access(child_id):
            return {'message': 'Not authorized to modify this child'}, 403

        child = Child.query.get(child_id)
        if not child:
            return {'message': 'Child not found'}, 404

        data = request.get_json()
        if not data:
            return {'message': 'No data provided'}, 400

        try:
            # Update user account info
            if child.user_account:
                if 'name' in data:
                    child.user_account.name = data['name']
                if 'email' in data:
                    child.user_account.email = data['email']

            # Update child-specific info
            if 'class_id' in data:
                child.class_id = data['class_id']

            db.session.commit()

            return {
                'id': child.id,
                'user_id': child.user_id,
                'name': child.user_account.name if child.user_account else None,
                'email': child.user_account.email if child.user_account else None,
                'total_balance': float(child.total_balance),
                'class_name': child.class_info.name if child.class_info else None,
                'goals_count': Goal.query.filter_by(child_id=child.id).count(),
                'recent_activity': []
            }, 200

        except Exception as e:
            db.session.rollback()
            return {'message': f'Error updating child: {str(e)}'}, 400

    def remove_child(self, child_id):
        """Remove child from parent's management"""
        if not self._check_child_access(child_id):
            return {'message': 'Not authorized to remove this child'}, 403

        parent = Parent.query.filter_by(user_id=current_user.id).first()
        if not parent:
            return {'message': 'Parent profile not found'}, 404

        link = ParentChildLink.query.filter_by(
            parent_id=parent.id,
            child_id=child_id
        ).first()

        if not link:
            return {'message': 'Child not linked to this parent'}, 404

        try:
            db.session.delete(link)
            db.session.commit()
            return {'message': 'Child removed from management successfully'}, 200
        except Exception as e:
            db.session.rollback()
            return {'message': f'Error removing child: {str(e)}'}, 400

    def _check_child_access(self, child_id):
        """Check if current user has access to this child"""
        if 'parent' not in current_user.roles:
            return False

        parent = Parent.query.filter_by(user_id=current_user.id).first()
        if not parent:
            return False

        link = ParentChildLink.query.filter_by(
            parent_id=parent.id,
            child_id=child_id
        ).first()

        return link is not None

class ChildOverviewApi(Resource):
    @auth_required('token')
    @cache.memoize(timeout=5)
    @marshal_with(child_overview_fields)
    def get(self, child_id):
        return self.fetch_child_overview(child_id)

    def fetch_child_overview(self, child_id):
        """Get comprehensive overview of a child's financial status"""
        if not self._check_child_access(child_id):
            return {'message': 'Not authorized to view this child'}, 403

        child = Child.query.get(child_id)
        if not child:
            return {'message': 'Child not found'}, 404

        # Get goals
        goals = Goal.query.filter_by(child_id=child_id).all()
        goals_data = []
        for goal in goals:
            progress = (float(child.total_balance) / float(goal.amount)) * 100 if goal.amount > 0 else 0
            goals_data.append({
                'id': goal.id,
                'title': goal.title,
                'amount': float(goal.amount),
                'deadline': goal.deadline.isoformat() if goal.deadline else None,
                'status': goal.status,
                'progress_percentage': min(100, progress)
            })

        # Get recent spending
        recent_spending = Spending.query.filter_by(child_id=child_id).order_by(
            desc(Spending.spend_date)
        ).limit(10).all()

        spending_data = []
        for spend in recent_spending:
            spending_data.append({
                'id': spend.id,
                'category': spend.category,
                'amount': float(spend.amount),
                'date': spend.spend_date.isoformat(),
                'description': spend.description
            })

        # Get money sources
        money_sources = PocketMoneyPlace.query.filter_by(child_id=child_id).all()
        sources_data = []
        for source in money_sources:
            sources_data.append({
                'id': source.id,
                'name': source.name,
                'amount': float(source.amount_stored)
            })

        # Get spending summary by category
        spending_summary = db.session.query(
            Spending.category,
            func.sum(Spending.amount).label('total'),
            func.count(Spending.id).label('count')
        ).filter_by(child_id=child_id).group_by(Spending.category).all()

        summary_data = {}
        for category, total, count in spending_summary:
            summary_data[category] = {
                'total': float(total),
                'count': count
            }

        # Get challenge progress
        completed_challenges = ChallengeProgress.query.filter_by(
            child_id=child_id,
            status='completed'
        ).count()

        total_challenges = ChallengeProgress.query.filter_by(child_id=child_id).count()

        return {
            'id': child.id,
            'name': child.user_account.name if child.user_account else None,
            'total_balance': float(child.total_balance),
            'goals': goals_data,
            'recent_spending': spending_data,
            'money_sources': sources_data,
            'spending_summary': summary_data,
            'achievement_progress': {
                'completed_challenges': completed_challenges,
                'total_challenges': total_challenges,
                'completion_rate': (completed_challenges / total_challenges * 100) if total_challenges > 0 else 0
            }
        }

    def _check_child_access(self, child_id):
        """Check if current user has access to this child"""
        if 'parent' not in current_user.roles:
            return False

        parent = Parent.query.filter_by(user_id=current_user.id).first()
        if not parent:
            return False

        link = ParentChildLink.query.filter_by(
            parent_id=parent.id,
            child_id=child_id
        ).first()

        return link is not None

# --------------------------Allowance Management-----------------------------
class AllowanceApi(Resource):
    @auth_required('token')
    @cache.cached(timeout=5)
    @marshal_with(allowance_fields)
    def get(self):
        return self.fetch_all_allowances()

    @auth_required('token')
    @marshal_with(allowance_fields)
    def post(self):
        return self.create_allowance()

    def fetch_all_allowances(self):
        """Get all allowances given by current parent"""
        if 'parent' not in current_user.roles:
            return {'message': 'Not authorized'}, 403

        parent = Parent.query.filter_by(user_id=current_user.id).first()
        if not parent:
            return {'message': 'Parent profile not found'}, 404

        allowances = PocketMoney.query.filter_by(parent_id=parent.id).all()
        allowances_data = []

        for allowance in allowances:
            allowances_data.append({
                'id': allowance.id,
                'child_id': allowance.child_id,
                'child_name': allowance.child.user_account.name if allowance.child and allowance.child.user_account else None,
                'amount': float(allowance.amount),
                'date_given': allowance.date_given.isoformat(),
                'recurring': allowance.recurring,
                'recurring_schedule': allowance.recurring_schedule,
                'stored_in': allowance.stored_in
            })

        return allowances_data

    def create_allowance(self):
        """Create new allowance for a child"""
        if 'parent' not in current_user.roles:
            return {'message': 'Not authorized'}, 403

        parent = Parent.query.filter_by(user_id=current_user.id).first()
        if not parent:
            return {'message': 'Parent profile not found'}, 404

        data = request.get_json()
        if not data:
            return {'message': 'No data provided'}, 400

        required_fields = ['child_id', 'amount', 'date_given']
        for field in required_fields:
            if field not in data:
                return {'message': f'Missing required field: {field}'}, 400

        # Verify child access
        if not self._check_child_access(data['child_id']):
            return {'message': 'Not authorized to give allowance to this child'}, 403

        try:
            allowance = PocketMoney(
                child_id=data['child_id'],
                parent_id=parent.id,
                amount=data['amount'],
                date_given=datetime.strptime(data['date_given'], '%Y-%m-%d').date(),
                recurring=data.get('recurring', False),
                recurring_schedule=data.get('recurring_schedule'),
                stored_in=data.get('stored_in')
            )

            # Update child's balance
            child = Child.query.get(data['child_id'])
            if child:
                child.total_balance += float(data['amount'])

            db.session.add(allowance)
            db.session.commit()

            return {
                'id': allowance.id,
                'child_id': allowance.child_id,
                'child_name': allowance.child.user_account.name if allowance.child and allowance.child.user_account else None,
                'amount': float(allowance.amount),
                'date_given': allowance.date_given.isoformat(),
                'recurring': allowance.recurring,
                'recurring_schedule': allowance.recurring_schedule,
                'stored_in': allowance.stored_in
            }, 201

        except Exception as e:
            db.session.rollback()
            return {'message': f'Error creating allowance: {str(e)}'}, 400

    def _check_child_access(self, child_id):
        """Check if current user has access to this child"""
        if 'parent' not in current_user.roles:
            return False

        parent = Parent.query.filter_by(user_id=current_user.id).first()
        if not parent:
            return False

        link = ParentChildLink.query.filter_by(
            parent_id=parent.id,
            child_id=child_id
        ).first()

        return link is not None

class AllowanceHistoryApi(Resource):
    @auth_required('token')
    @cache.cached(timeout=5)
    @marshal_with(allowance_fields)
    def get(self):
        return self.fetch_allowance_history()

    def fetch_allowance_history(self):
        """Get allowance history with filtering"""
        if 'parent' not in current_user.roles:
            return {'message': 'Not authorized'}, 403

        parent = Parent.query.filter_by(user_id=current_user.id).first()
        if not parent:
            return {'message': 'Parent profile not found'}, 404

        # Get query parameters
        child_id = request.args.get('child_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', 50, type=int)

        query = PocketMoney.query.filter_by(parent_id=parent.id)

        if child_id:
            query = query.filter(PocketMoney.child_id == child_id)
        if start_date:
            query = query.filter(PocketMoney.date_given >= datetime.strptime(start_date, '%Y-%m-%d').date())
        if end_date:
            query = query.filter(PocketMoney.date_given <= datetime.strptime(end_date, '%Y-%m-%d').date())

        allowances = query.order_by(desc(PocketMoney.date_given)).limit(limit).all()

        history_data = []
        for allowance in allowances:
            history_data.append({
                'id': allowance.id,
                'child_id': allowance.child_id,
                'child_name': allowance.child.user_account.name if allowance.child and allowance.child.user_account else None,
                'amount': float(allowance.amount),
                'date_given': allowance.date_given.isoformat(),
                'recurring': allowance.recurring,
                'recurring_schedule': allowance.recurring_schedule,
                'stored_in': allowance.stored_in
            })

        return history_data

# --------------------------Reports-----------------------------
class ReportSummaryApi(Resource):
    @auth_required('token')
    @cache.cached(timeout=10)
    @marshal_with(report_fields)
    def get(self):
        return self.fetch_summary_report()

    def fetch_summary_report(self):
        """Get comprehensive summary report"""
        if 'parent' not in current_user.roles:
            return {'message': 'Not authorized'}, 403

        parent = Parent.query.filter_by(user_id=current_user.id).first()
        if not parent:
            return {'message': 'Parent profile not found'}, 404

        # Get all children
        children_links = ParentChildLink.query.filter_by(parent_id=parent.id).all()
        children_data = []
        total_balance = 0
        total_spent = 0
        total_allowances = 0

        for link in children_links:
            child = link.child
            if child:
                child_spending = db.session.query(func.sum(Spending.amount)).filter_by(child_id=child.id).scalar() or 0
                child_allowances = db.session.query(func.sum(PocketMoney.amount)).filter_by(child_id=child.id).scalar() or 0
                
                total_balance += float(child.total_balance)
                total_spent += float(child_spending)
                total_allowances += float(child_allowances)

                children_data.append({
                    'id': child.id,
                    'name': child.user_account.name if child.user_account else None,
                    'balance': float(child.total_balance),
                    'spent': float(child_spending),
                    'allowances_received': float(child_allowances)
                })

        return {
            'summary': {
                'total_children': len(children_data),
                'total_balance': total_balance,
                'total_spent': total_spent,
                'total_allowances_given': total_allowances,
                'average_balance': total_balance / len(children_data) if children_data else 0
            },
            'children_data': children_data,
            'generated_at': datetime.now().isoformat()
        }

# --------------------------Messaging-----------------------------
class MessageApi(Resource):
    @auth_required('token')
    @cache.cached(timeout=5)
    @marshal_with(message_fields)
    def get(self):
        return self.fetch_messages()

    @auth_required('token')
    @marshal_with(message_fields)
    def post(self):
        return self.send_message()

    def fetch_messages(self):
        """Get messages (inbox or sent based on query parameter)"""
        if 'parent' not in current_user.roles:
            return {'message': 'Not authorized'}, 403

        message_type = request.args.get('type', 'inbox')  # 'inbox' or 'sent'
        
        if message_type == 'sent':
            messages = NotesEncouragement.query.filter_by(sender_id=current_user.id).order_by(
                desc(NotesEncouragement.date_sent)
            ).all()
        else:
            # For inbox, get messages sent to children under this parent
            parent = Parent.query.filter_by(user_id=current_user.id).first()
            if not parent:
                return {'message': 'Parent profile not found'}, 404

            children_ids = [link.child_id for link in ParentChildLink.query.filter_by(parent_id=parent.id).all()]
            messages = NotesEncouragement.query.filter(
                NotesEncouragement.child_id.in_(children_ids)
            ).order_by(desc(NotesEncouragement.date_sent)).all()

        messages_data = []
        for message in messages:
            messages_data.append({
                'id': message.id,
                'sender_id': message.sender_id,
                'child_id': message.child_id,
                'sender_name': message.sender.name if message.sender else None,
                'child_name': message.child.user_account.name if message.child and message.child.user_account else None,
                'message': message.message,
                'date_sent': message.date_sent.isoformat()
            })

        return messages_data

    def send_message(self):
        """Send encouragement message to child"""
        if 'parent' not in current_user.roles:
            return {'message': 'Not authorized'}, 403

        data = request.get_json()
        if not data:
            return {'message': 'No data provided'}, 400

        required_fields = ['child_id', 'message']
        for field in required_fields:
            if field not in data:
                return {'message': f'Missing required field: {field}'}, 400

        # Verify child access
        if not self._check_child_access(data['child_id']):
            return {'message': 'Not authorized to send message to this child'}, 403

        try:
            message = NotesEncouragement(
                sender_id=current_user.id,
                child_id=data['child_id'],
                message=data['message']
            )

            db.session.add(message)
            db.session.commit()

            return {
                'id': message.id,
                'sender_id': message.sender_id,
                'child_id': message.child_id,
                'sender_name': current_user.name,
                'child_name': message.child.user_account.name if message.child and message.child.user_account else None,
                'message': message.message,
                'date_sent': message.date_sent.isoformat()
            }, 201

        except Exception as e:
            db.session.rollback()
            return {'message': f'Error sending message: {str(e)}'}, 400

    def _check_child_access(self, child_id):
        """Check if current user has access to this child"""
        if 'parent' not in current_user.roles:
            return False

        parent = Parent.query.filter_by(user_id=current_user.id).first()
        if not parent:
            return False

        link = ParentChildLink.query.filter_by(
            parent_id=parent.id,
            child_id=child_id
        ).first()

        return link is not None

# Register API routes
parent_api.add_resource(ChildrenApi, '/children')
parent_api.add_resource(ChildApi, '/children/<int:child_id>')
parent_api.add_resource(ChildOverviewApi, '/children/<int:child_id>/overview')
parent_api.add_resource(AllowanceApi, '/allowances')
parent_api.add_resource(AllowanceHistoryApi, '/allowances/history')
parent_api.add_resource(ReportSummaryApi, '/reports/summary')
parent_api.add_resource(MessageApi, '/messages')

def register_parent_routes(app):
    parent_api.init_app(app)
