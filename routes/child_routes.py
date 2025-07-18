from flask import Blueprint, jsonify, request, g
from datetime import datetime, date
from sqlalchemy.exc import IntegrityError
from sqlalchemy import func, desc, and_
import json

# Import your models here
from models import (
    db, User, Child, Parent, Goal, Spending, PocketMoney, 
    PocketMoneyPlace, PocketMoneyLog, Challenge, ChallengeProgress,
    NotesEncouragement
)

child_bp = Blueprint('child', __name__)

# Helper function to get current child
def get_current_child():
    """Get the current child from session/auth context"""
    # This would typically come from your authentication system
    # For now, assuming child_id is passed in headers or session
    child_id = request.headers.get('Child-ID')
    if not child_id:
        return None
    return Child.query.get(child_id)

# Helper function for error responses
def error_response(message, status_code=400):
    return jsonify({'error': message}), status_code

def success_response(data=None, message="Success", status_code=200):
    response = {'message': message}
    if data:
        response['data'] = data
    return jsonify(response), status_code

# --- Goals Management ---
@child_bp.route('/goals', methods=['GET'])
def get_goals():
    """Get all goals for the current child"""
    child = get_current_child()
    if not child:
        return error_response("Child not found", 404)
    
    goals = Goal.query.filter_by(child_id=child.id).all()
    
    goals_data = []
    for goal in goals:
        # Calculate progress based on current balance vs goal amount
        progress_percentage = min(100, (float(child.total_balance) / float(goal.amount)) * 100) if goal.amount > 0 else 0
        
        goals_data.append({
            'id': goal.id,
            'title': goal.title,
            'amount': float(goal.amount),
            'deadline': goal.deadline.isoformat() if goal.deadline else None,
            'status': goal.status,
            'progress_percentage': round(progress_percentage, 2),
            'amount_needed': max(0, float(goal.amount) - float(child.total_balance))
        })
    
    return success_response(goals_data)

@child_bp.route('/goals', methods=['POST'])
def create_goal():
    """Create a new goal"""
    child = get_current_child()
    if not child:
        return error_response("Child not found", 404)
    
    data = request.get_json()
    if not data:
        return error_response("No data provided")
    
    # Validate required fields
    required_fields = ['title', 'amount']
    for field in required_fields:
        if field not in data:
            return error_response(f"Missing required field: {field}")
    
    try:
        goal = Goal(
            child_id=child.id,
            title=data['title'],
            amount=data['amount'],
            deadline=datetime.strptime(data['deadline'], '%Y-%m-%d').date() if data.get('deadline') else None,
            status='active'
        )
        
        db.session.add(goal)
        db.session.commit()
        
        return success_response({
            'id': goal.id,
            'title': goal.title,
            'amount': float(goal.amount),
            'deadline': goal.deadline.isoformat() if goal.deadline else None,
            'status': goal.status
        }, "Goal created successfully", 201)
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Error creating goal: {str(e)}")

@child_bp.route('/goals/<int:goal_id>', methods=['GET'])
def get_goal(goal_id):
    """Get a specific goal"""
    child = get_current_child()
    if not child:
        return error_response("Child not found", 404)
    
    goal = Goal.query.filter_by(id=goal_id, child_id=child.id).first()
    if not goal:
        return error_response("Goal not found", 404)
    
    progress_percentage = min(100, (float(child.total_balance) / float(goal.amount)) * 100) if goal.amount > 0 else 0
    
    goal_data = {
        'id': goal.id,
        'title': goal.title,
        'amount': float(goal.amount),
        'deadline': goal.deadline.isoformat() if goal.deadline else None,
        'status': goal.status,
        'progress_percentage': round(progress_percentage, 2),
        'amount_needed': max(0, float(goal.amount) - float(child.total_balance))
    }
    
    return success_response(goal_data)

@child_bp.route('/goals/<int:goal_id>', methods=['PUT'])
def update_goal(goal_id):
    """Update a goal"""
    child = get_current_child()
    if not child:
        return error_response("Child not found", 404)
    
    goal = Goal.query.filter_by(id=goal_id, child_id=child.id).first()
    if not goal:
        return error_response("Goal not found", 404)
    
    data = request.get_json()
    if not data:
        return error_response("No data provided")
    
    try:
        if 'title' in data:
            goal.title = data['title']
        if 'amount' in data:
            goal.amount = data['amount']
        if 'deadline' in data:
            goal.deadline = datetime.strptime(data['deadline'], '%Y-%m-%d').date() if data['deadline'] else None
        if 'status' in data:
            goal.status = data['status']
        
        db.session.commit()
        
        return success_response({
            'id': goal.id,
            'title': goal.title,
            'amount': float(goal.amount),
            'deadline': goal.deadline.isoformat() if goal.deadline else None,
            'status': goal.status
        }, "Goal updated successfully")
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Error updating goal: {str(e)}")

@child_bp.route('/goals/<int:goal_id>', methods=['DELETE'])
def delete_goal(goal_id):
    """Delete a goal"""
    child = get_current_child()
    if not child:
        return error_response("Child not found", 404)
    
    goal = Goal.query.filter_by(id=goal_id, child_id=child.id).first()
    if not goal:
        return error_response("Goal not found", 404)
    
    try:
        db.session.delete(goal)
        db.session.commit()
        return success_response(message="Goal deleted successfully")
    except Exception as e:
        db.session.rollback()
        return error_response(f"Error deleting goal: {str(e)}")

@child_bp.route('/goals/<int:goal_id>/progress', methods=['PATCH'])
def patch_goal_progress(goal_id):
    """Update goal progress/status"""
    child = get_current_child()
    if not child:
        return error_response("Child not found", 404)
    
    goal = Goal.query.filter_by(id=goal_id, child_id=child.id).first()
    if not goal:
        return error_response("Goal not found", 404)
    
    data = request.get_json()
    if not data:
        return error_response("No data provided")
    
    try:
        if 'status' in data:
            goal.status = data['status']
        
        db.session.commit()
        
        # Calculate current progress
        progress_percentage = min(100, (float(child.total_balance) / float(goal.amount)) * 100) if goal.amount > 0 else 0
        
        return success_response({
            'id': goal.id,
            'status': goal.status,
            'progress_percentage': round(progress_percentage, 2)
        }, "Goal progress updated successfully")
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Error updating goal progress: {str(e)}")

# --- Spending ---
@child_bp.route('/spends', methods=['GET'])
def get_spends():
    """Get all spending records for the current child"""
    child = get_current_child()
    if not child:
        return error_response("Child not found", 404)
    
    # Get query parameters for filtering
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
    
    spends = query.order_by(desc(Spending.spend_date)).limit(limit).all()
    
    spends_data = []
    for spend in spends:
        spends_data.append({
            'id': spend.id,
            'category': spend.category,
            'amount': float(spend.amount),
            'spend_date': spend.spend_date.isoformat(),
            'description': spend.description
        })
    
    # Calculate total spending
    total_spent = sum(float(spend.amount) for spend in spends)
    
    return success_response({
        'spends': spends_data,
        'total_spent': total_spent,
        'count': len(spends_data)
    })

@child_bp.route('/spends', methods=['POST'])
def create_spend():
    """Create a new spending record"""
    child = get_current_child()
    if not child:
        return error_response("Child not found", 404)
    
    data = request.get_json()
    if not data:
        return error_response("No data provided")
    
    # Validate required fields
    required_fields = ['category', 'amount', 'spend_date']
    for field in required_fields:
        if field not in data:
            return error_response(f"Missing required field: {field}")
    
    # Check if child has enough balance
    if float(data['amount']) > float(child.total_balance):
        return error_response("Insufficient balance")
    
    try:
        spend = Spending(
            child_id=child.id,
            category=data['category'],
            amount=data['amount'],
            spend_date=datetime.strptime(data['spend_date'], '%Y-%m-%d').date(),
            description=data.get('description', '')
        )
        
        # Update child's balance
        child.total_balance -= float(data['amount'])
        
        db.session.add(spend)
        db.session.commit()
        
        return success_response({
            'id': spend.id,
            'category': spend.category,
            'amount': float(spend.amount),
            'spend_date': spend.spend_date.isoformat(),
            'description': spend.description,
            'new_balance': float(child.total_balance)
        }, "Spending recorded successfully", 201)
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Error creating spending record: {str(e)}")

@child_bp.route('/spends/<int:spend_id>', methods=['GET'])
def get_spend(spend_id):
    """Get a specific spending record"""
    child = get_current_child()
    if not child:
        return error_response("Child not found", 404)
    
    spend = Spending.query.filter_by(id=spend_id, child_id=child.id).first()
    if not spend:
        return error_response("Spending record not found", 404)
    
    spend_data = {
        'id': spend.id,
        'category': spend.category,
        'amount': float(spend.amount),
        'spend_date': spend.spend_date.isoformat(),
        'description': spend.description
    }
    
    return success_response(spend_data)

@child_bp.route('/spends/<int:spend_id>', methods=['PUT'])
def update_spend(spend_id):
    """Update a spending record"""
    child = get_current_child()
    if not child:
        return error_response("Child not found", 404)
    
    spend = Spending.query.filter_by(id=spend_id, child_id=child.id).first()
    if not spend:
        return error_response("Spending record not found", 404)
    
    data = request.get_json()
    if not data:
        return error_response("No data provided")
    
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
        
        return success_response({
            'id': spend.id,
            'category': spend.category,
            'amount': float(spend.amount),
            'spend_date': spend.spend_date.isoformat(),
            'description': spend.description,
            'new_balance': float(child.total_balance)
        }, "Spending record updated successfully")
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Error updating spending record: {str(e)}")

@child_bp.route('/spends/<int:spend_id>', methods=['DELETE'])
def delete_spend(spend_id):
    """Delete a spending record"""
    child = get_current_child()
    if not child:
        return error_response("Child not found", 404)
    
    spend = Spending.query.filter_by(id=spend_id, child_id=child.id).first()
    if not spend:
        return error_response("Spending record not found", 404)
    
    try:
        # Restore balance
        child.total_balance += float(spend.amount)
        
        db.session.delete(spend)
        db.session.commit()
        
        return success_response({
            'new_balance': float(child.total_balance)
        }, "Spending record deleted successfully")
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Error deleting spending record: {str(e)}")

@child_bp.route('/spends/categories', methods=['GET'])
def get_spend_categories():
    """Get spending categories with statistics"""
    child = get_current_child()
    if not child:
        return error_response("Child not found", 404)
    
    # Get categories with spending totals
    categories = db.session.query(
        Spending.category,
        func.sum(Spending.amount).label('total_amount'),
        func.count(Spending.id).label('count')
    ).filter_by(child_id=child.id).group_by(Spending.category).all()
    
    categories_data = []
    for category, total_amount, count in categories:
        categories_data.append({
            'category': category,
            'total_amount': float(total_amount),
            'count': count
        })
    
    # Default categories if none exist
    default_categories = [
        'Food & Drinks', 'Entertainment', 'Toys & Games', 'Books & Education',
        'Clothes', 'Savings', 'Gifts', 'Other'
    ]
    
    return success_response({
        'used_categories': categories_data,
        'suggested_categories': default_categories
    })

# --- Pocket Money ---
@child_bp.route('/money-sources', methods=['GET'])
def get_money_sources():
    """Get all money storage places for the current child"""
    child = get_current_child()
    if not child:
        return error_response("Child not found", 404)
    
    places = PocketMoneyPlace.query.filter_by(child_id=child.id).all()
    
    places_data = []
    for place in places:
        places_data.append({
            'id': place.id,
            'name': place.name,
            'amount_stored': float(place.amount_stored)
        })
    
    return success_response(places_data)

@child_bp.route('/money-sources', methods=['POST'])
def create_money_source():
    """Create a new money storage place"""
    child = get_current_child()
    if not child:
        return error_response("Child not found", 404)
    
    data = request.get_json()
    if not data:
        return error_response("No data provided")
    
    if 'name' not in data:
        return error_response("Missing required field: name")
    
    try:
        place = PocketMoneyPlace(
            child_id=child.id,
            name=data['name'],
            amount_stored=data.get('amount_stored', 0.00)
        )
        
        db.session.add(place)
        db.session.commit()
        
        return success_response({
            'id': place.id,
            'name': place.name,
            'amount_stored': float(place.amount_stored)
        }, "Money source created successfully", 201)
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Error creating money source: {str(e)}")

@child_bp.route('/money-sources/<int:source_id>', methods=['PUT'])
def update_money_source(source_id):
    """Update a money storage place"""
    child = get_current_child()
    if not child:
        return error_response("Child not found", 404)
    
    place = PocketMoneyPlace.query.filter_by(id=source_id, child_id=child.id).first()
    if not place:
        return error_response("Money source not found", 404)
    
    data = request.get_json()
    if not data:
        return error_response("No data provided")
    
    try:
        if 'name' in data:
            place.name = data['name']
        if 'amount_stored' in data:
            place.amount_stored = data['amount_stored']
        
        db.session.commit()
        
        return success_response({
            'id': place.id,
            'name': place.name,
            'amount_stored': float(place.amount_stored)
        }, "Money source updated successfully")
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Error updating money source: {str(e)}")

@child_bp.route('/money-sources/<int:source_id>', methods=['DELETE'])
def delete_money_source(source_id):
    """Delete a money storage place"""
    child = get_current_child()
    if not child:
        return error_response("Child not found", 404)
    
    place = PocketMoneyPlace.query.filter_by(id=source_id, child_id=child.id).first()
    if not place:
        return error_response("Money source not found", 404)
    
    try:
        db.session.delete(place)
        db.session.commit()
        return success_response(message="Money source deleted successfully")
    except Exception as e:
        db.session.rollback()
        return error_response(f"Error deleting money source: {str(e)}")

@child_bp.route('/balance', methods=['GET'])
def get_balance():
    """Get child's current balance and breakdown"""
    child = get_current_child()
    if not child:
        return error_response("Child not found", 404)
    
    # Get money places breakdown
    places = PocketMoneyPlace.query.filter_by(child_id=child.id).all()
    places_breakdown = []
    for place in places:
        places_breakdown.append({
            'name': place.name,
            'amount': float(place.amount_stored)
        })
    
    # Get recent transactions
    recent_logs = PocketMoneyLog.query.filter_by(child_id=child.id).order_by(desc(PocketMoneyLog.date)).limit(5).all()
    recent_transactions = []
    for log in recent_logs:
        recent_transactions.append({
            'amount': float(log.amount),
            'date': log.date.isoformat(),
            'description': log.description if hasattr(log, 'description') else 'Transaction'
        })
    
    return success_response({
        'total_balance': float(child.total_balance),
        'places_breakdown': places_breakdown,
        'recent_transactions': recent_transactions
    })

# --- Challenges ---
@child_bp.route('/challenges/current', methods=['GET'])
def get_current_challenges():
    """Get current active challenges"""
    child = get_current_child()
    if not child:
        return error_response("Child not found", 404)
    
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
        
        challenges_data.append({
            'id': challenge.id,
            'title': challenge.title,
            'description': challenge.description,
            'reward': challenge.reward,
            'ends_on': challenge.ends_on.isoformat(),
            'status': progress.status if progress else 'available',
            'has_started': progress is not None
        })
    
    return success_response(challenges_data)

@child_bp.route('/challenges/history', methods=['GET'])
def get_challenge_history():
    """Get challenge history for the child"""
    child = get_current_child()
    if not child:
        return error_response("Child not found", 404)
    
    # Get child's challenge progress
    progress_records = db.session.query(
        ChallengeProgress, Challenge
    ).join(Challenge).filter(
        ChallengeProgress.child_id == child.id
    ).order_by(desc(Challenge.created_on)).all()
    
    history_data = []
    for progress, challenge in progress_records:
        history_data.append({
            'challenge_id': challenge.id,
            'title': challenge.title,
            'description': challenge.description,
            'reward': challenge.reward,
            'status': progress.status,
            'started_on': challenge.created_on.isoformat(),
            'ended_on': challenge.ends_on.isoformat() if challenge.ends_on else None
        })
    
    return success_response(history_data)

@child_bp.route('/challenges/<int:challenge_id>/complete', methods=['POST'])
def complete_challenge(challenge_id):
    """Mark a challenge as completed"""
    child = get_current_child()
    if not child:
        return error_response("Child not found", 404)
    
    challenge = Challenge.query.get(challenge_id)
    if not challenge:
        return error_response("Challenge not found", 404)
    
    # Check if challenge is still active
    if challenge.ends_on and challenge.ends_on < datetime.now():
        return error_response("Challenge has expired")
    
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
        
        return success_response({
            'challenge_id': challenge_id,
            'status': 'completed',
            'reward': challenge.reward
        }, "Challenge completed successfully")
        
    except Exception as e:
        db.session.rollback()
        return error_response(f"Error completing challenge: {str(e)}")

# --- Tips ---
@child_bp.route('/tips/weekly', methods=['GET'])
def get_weekly_tips():
    """Get weekly financial tips"""
    # This could be from a database or static content
    weekly_tips = [
        {
            'id': 1,
            'title': 'Save Before You Spend',
            'content': 'Always put aside some money for savings before spending on wants.',
            'category': 'saving',
            'week': datetime.now().isocalendar()[1]
        },
        {
            'id': 2,
            'title': 'Compare Prices',
            'content': 'Before buying something, check if you can find it for less money elsewhere.',
            'category': 'smart_spending',
            'week': datetime.now().isocalendar()[1]
        },
        {
            'id': 3,
            'title': 'Track Your Spending',
            'content': 'Keep track of where your money goes to make better spending decisions.',
            'category': 'budgeting',
            'week': datetime.now().isocalendar()[1]
        }
    ]
    
    return success_response(weekly_tips)

@child_bp.route('/tips/archive', methods=['GET'])
def get_tip_archive():
    """Get archived tips"""
    # This could be from a database with historical tips
    archived_tips = [
        {
            'id': 1,
            'title': 'The 50/30/20 Rule',
            'content': 'Spend 50% on needs, 30% on wants, and save 20%.',
            'category': 'budgeting',
            'week': datetime.now().isocalendar()[1] - 1
        },
        {
            'id': 2,
            'title': 'Emergency Fund',
            'content': 'Always keep some money aside for unexpected expenses.',
            'category': 'saving',
            'week': datetime.now().isocalendar()[1] - 2
        }
    ]
    
    return success_response(archived_tips)