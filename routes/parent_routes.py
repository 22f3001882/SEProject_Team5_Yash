from flask import Blueprint, jsonify, request

parent_bp = Blueprint('parent', __name__)

# Children Management
@parent_bp.route('/children', methods=['GET'])
def get_children():
    return jsonify({'message': 'Get all children'})

@parent_bp.route('/children', methods=['POST'])
def create_child():
    return jsonify({'message': 'Create new child'})

@parent_bp.route('/children/<int:child_id>', methods=['GET'])
def get_child(child_id):
    return jsonify({'message': f'Get child {child_id}'})

@parent_bp.route('/children/<int:child_id>', methods=['PUT'])
def update_child(child_id):
    return jsonify({'message': f'Update child {child_id}'})

@parent_bp.route('/children/<int:child_id>', methods=['DELETE'])
def delete_child(child_id):
    return jsonify({'message': f'Delete child {child_id}'})

@parent_bp.route('/children/<int:child_id>/overview', methods=['GET'])
def get_child_overview(child_id):
    return jsonify({'message': f'Overview for child {child_id}'})

# Allowance Management
@parent_bp.route('/allowances', methods=['GET'])
def get_allowances():
    return jsonify({'message': 'Get all allowances'})

@parent_bp.route('/allowances', methods=['POST'])
def create_allowance():
    return jsonify({'message': 'Create allowance'})

@parent_bp.route('/allowances/history', methods=['GET'])
def get_allowance_history():
    return jsonify({'message': 'Get allowance history'})

@parent_bp.route('/allowances/<int:allowance_id>', methods=['PUT'])
def update_allowance(allowance_id):
    return jsonify({'message': f'Update allowance {allowance_id}'})

@parent_bp.route('/allowances/<int:allowance_id>', methods=['DELETE'])
def delete_allowance(allowance_id):
    return jsonify({'message': f'Delete allowance {allowance_id}'})

# Reports
@parent_bp.route('/reports/summary', methods=['GET'])
def get_report_summary():
    return jsonify({'message': 'Get summary report'})

@parent_bp.route('/reports/children-progress', methods=['GET'])
def get_children_progress():
    return jsonify({'message': 'Get children progress report'})

@parent_bp.route('/reports/spending-trends', methods=['GET'])
def get_spending_trends():
    return jsonify({'message': 'Get spending trends report'})

@parent_bp.route('/reports/transactions', methods=['GET'])
def get_transactions_report():
    return jsonify({'message': 'Get transactions report'})

# Messaging
@parent_bp.route('/messages/inbox', methods=['GET'])
def get_inbox_messages():
    return jsonify({'message': 'Get inbox messages'})

@parent_bp.route('/messages/sent', methods=['GET'])
def get_sent_messages():
    return jsonify({'message': 'Get sent messages'})

@parent_bp.route('/messages', methods=['POST'])
def send_message():
    return jsonify({'message': 'Send new message'})

@parent_bp.route('/messages/<int:message_id>', methods=['GET'])
def get_message(message_id):
    return jsonify({'message': f'Get message {message_id}'})

@parent_bp.route('/messages/<int:message_id>', methods=['DELETE'])
def delete_message(message_id):
    return jsonify({'message': f'Delete message {message_id}'})