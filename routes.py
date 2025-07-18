from flask import current_app as app, jsonify, render_template, request, send_file
from flask_security import auth_required, verify_password, hash_password, current_user
from models import db
from datetime import datetime
# from backend.celery.tasks import add, create_quiz_csv
# from celery.result import AsyncResult

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

# @app.get('/get-celery-data/<id>')
# def getCeleryData(id):
#     result = AsyncResult(id)

#     if result.ready():
#         return {'result':result.result}
#     else:
#         return {'message':'task aint ready yet'}, 405

# -------------------------------

# @app.route('/create-quiz-csv')
# @auth_required('token')
# def createQuizCSV():
#     task = create_quiz_csv.delay(current_user.id)
#     return {'task_id': task.id}, 200

# @app.get('/get-quiz-csv/<id>')
# def getQuizData(id):
#     result = AsyncResult(id)
#     if result.ready():
#         if (result.result) == None:
#             return {'message':'No quiz'}, 405
#         return send_file('./backend/celery/user-downloads/'+str(result.result)), 200
#     else:
#         return {'message':'task aint ready yet'}, 405

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
