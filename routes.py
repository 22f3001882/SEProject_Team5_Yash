from flask import current_app as app, jsonify, render_template, request, send_file
from flask_security import auth_required, verify_password, hash_password, current_user
from models import db
from datetime import datetime
from backend_celery.tasks import (
    create_child_financial_report,
    send_daily_spending_reminders,
    send_weekly_spending_reminders,
    send_weekly_parent_summaries,
    process_recurring_allowances
)
from celery.result import AsyncResult

datastore = app.security.datastore
cache = app.cache

@app.get('/')
@cache.cached(timeout=300) 
def home():
    return render_template('index.html')

# ----------------------

# @app.route('/celery')
# def celery():
#     task = add.delay(50,60)
#     return {'task_id': task.id}, 200



@app.route('/trigger-daily-reminders')
@auth_required('token')
def trigger_daily_reminders():
    """Manually trigger daily spending reminders (for testing/admin)"""
    if 'admin' not in current_user.roles:
        return {'message': 'Not authorized'}, 403
    
    task = send_daily_spending_reminders.delay()
    return {'task_id': task.id, 'message': 'Daily reminders triggered'}, 200

@app.route('/trigger-weekly-reminders')
@auth_required('token')
def trigger_weekly_reminders():
    """Manually trigger weekly spending reminders (for testing/admin)"""
    if 'admin' not in current_user.roles:
        return {'message': 'Not authorized'}, 403
    
    task = send_weekly_spending_reminders.delay()
    return {'task_id': task.id, 'message': 'Weekly reminders triggered'}, 200

@app.route('/trigger-parent-summaries')
@auth_required('token')
def trigger_parent_summaries():
    """Manually trigger weekly parent summaries (for testing/admin)"""
    if 'admin' not in current_user.roles:
        return {'message': 'Not authorized'}, 403
    
    task = send_weekly_parent_summaries.delay()
    return {'task_id': task.id, 'message': 'Parent summaries triggered'}, 200

@app.route('/trigger-recurring-allowances')
@auth_required('token')
def trigger_recurring_allowances():
    """Manually trigger recurring allowances processing (for testing/admin)"""
    if 'admin' not in current_user.roles:
        return {'message': 'Not authorized'}, 403
    
    task = process_recurring_allowances.delay()
    return {'task_id': task.id, 'message': 'Recurring allowances processing triggered'}, 200

# ----------------------------------------------

@app.route('/cache')
@cache.cached(timeout=5)
def cache():
    return {'time': str(datetime.now())}

@app.get('/protected_route')
@auth_required('token')
def protected():
    return '<h1>Protected Route Page</h1>'

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'missing inputs'}), 400
    
    user = datastore.find_user(email=email)

    if not user:
        return jsonify({'message': "user doesn't exist"}), 400

    if not verify_password(password, user.password):
        return jsonify({'message': "wrong password"}), 400
    else:
        return jsonify({'token': user.get_auth_token(), 'email':user.email, 'role': user.roles[0].name, 'id':user.id})
    

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    role = data.get('role')
    if role not in ['school', 'child', 'parent', 'teacher']:
        return jsonify({'message': "role doesn't exist"}), 400

    
    if not email or not password:
        return jsonify({'message': 'missing inputs'}), 400
    
    user = datastore.find_user(email = email)
    if user:
        return jsonify({'message': "User with email already exists"}), 400
    user = datastore.find_user(email = email)
    if user:
        return jsonify({'message': "User with this Email already exists"}), 400
    
    try:
        datastore.create_user(email= email, password=hash_password(password), name=name, roles = [role])
        db.session.commit()
        return jsonify({'message': "User created successfully!"}), 200
    except Exception as e:
        print("Error during user creation:", e)
        db.session.rollback()
        return jsonify({'message': "User was NOT created"}), 400


@app.route('/register/child', methods=['POST'])
def register_child():
    """Register a new child user and create child profile"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['email', 'password', 'name', 'class_id']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}), 400
    
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    class_id = data.get('class_id')
    
    # Check if user already exists
    user = datastore.find_user(email=email)
    if user:
        return jsonify({'message': "User with this email already exists"}), 400
    
    # Validate class exists
    from models import Class
    class_obj = Class.query.get(class_id)
    if not class_obj:
        return jsonify({'message': "Class not found"}), 400
    
    try:
        # Create user account
        user = datastore.create_user(
            email=email, 
            password=hash_password(password), 
            name=name, 
            roles=['child']
        )
        db.session.flush()  # Get the user ID
        
        # Create child profile
        from models import Child
        child = Child(
            user_id=user.id,
            class_id=class_id,
            total_balance=0.00
        )
        
        db.session.add(child)
        db.session.commit()
        
        return jsonify({
            'message': 'Child registered successfully!',
            'user_id': user.id,
            'child_id': child.id
        }), 201
        
    except Exception as e:
        print("Error during child registration:", e)
        db.session.rollback()
        return jsonify({'message': "Child registration failed"}), 400


@app.route('/register/parent', methods=['POST'])
def register_parent():
    """Register a new parent user and create parent profile"""
    data = request.get_json()
    
    # Validate required fields
    required_fields = ['email', 'password', 'name']
    for field in required_fields:
        if field not in data:
            return jsonify({'message': f'Missing required field: {field}'}), 400
    
    email = data.get('email')
    password = data.get('password')
    name = data.get('name')
    
    # Check if user already exists
    user = datastore.find_user(email=email)
    if user:
        return jsonify({'message': "User with this email already exists"}), 400
    
    try:
        # Create user account
        user = datastore.create_user(
            email=email, 
            password=hash_password(password), 
            name=name, 
            roles=['parent']
        )
        db.session.flush()  # Get the user ID
        
        # Create parent profile
        from models import Parent
        parent = Parent(user_id=user.id)
        
        db.session.add(parent)
        db.session.commit()
        
        return jsonify({
            'message': 'Parent registered successfully!',
            'user_id': user.id,
            'parent_id': parent.id
        }), 201
        
    except Exception as e:
        print("Error during parent registration:", e)
        db.session.rollback()
        return jsonify({'message': "Parent registration failed"}), 400