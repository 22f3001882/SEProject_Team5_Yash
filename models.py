from flask import Flask, request, jsonify, g
from flask_security import UserMixin, RoleMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date
import sqlite3, os, pytz


IST = pytz.timezone('Asia/Kolkata')


db = SQLAlchemy()



class User(db.Model, UserMixin):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # Will store hashed password
    fs_uniquifier = db.Column(db.String, unique=True, nullable=False)
    active = db.Column(db.Boolean, default=True)
    roles = db.relationship('Role', backref='user', secondary= 'user_roles')
    # Relationships
    children = db.relationship('Child', backref='user_account', lazy=True)
    parents = db.relationship('Parent', backref='user_account', lazy=True)
    teachers = db.relationship('Teacher', backref='user_account', lazy=True)
    schools = db.relationship('School', backref='user_account', lazy=True)

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, unique=True, nullable = False)
    description = db.Column(db.String, nullable = False)

class UserRoles(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'))

class School(db.Model):
    __tablename__ = 'schools'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.String(500))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    classes = db.relationship('Class', backref='school', lazy=True)
    teachers = db.relationship('Teacher', backref='school', lazy=True)

class Child(db.Model):
    __tablename__ = 'children'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.id'))
    total_balance = db.Column(db.Numeric(10, 2), default=0.00)
    
    # Relationships
    parent_links = db.relationship('ParentChildLink', backref='child', lazy=True)
    pocket_money = db.relationship('PocketMoney', backref='child', lazy=True)
    pocket_money_logs = db.relationship('PocketMoneyLog', backref='child', lazy=True)
    pocket_money_places = db.relationship('PocketMoneyPlace', backref='child', lazy=True)
    goals = db.relationship('Goal', backref='child', lazy=True)
    spendings = db.relationship('Spending', backref='child', lazy=True)
    challenge_progress = db.relationship('ChallengeProgress', backref='child', lazy=True)
    notes_received = db.relationship('NotesEncouragement', backref='child', lazy=True)

class Parent(db.Model):
    __tablename__ = 'parents'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationships
    child_links = db.relationship('ParentChildLink', backref='parent', lazy=True)
    pocket_money_given = db.relationship('PocketMoney', backref='parent', lazy=True)

class Teacher(db.Model):
    __tablename__ = 'teachers'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    
    # Relationships
    classes = db.relationship('Class', backref='teacher', lazy=True)

class Class(db.Model):
    __tablename__ = 'classes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('teachers.id'), nullable=False)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    
    # Relationships
    students = db.relationship('Child', backref='class_info', lazy=True)

class ParentChildLink(db.Model):
    __tablename__ = 'parent_child_links'
    
    parent_id = db.Column(db.Integer, db.ForeignKey('parents.id'), primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.id'), primary_key=True)
    primary = db.Column(db.Boolean, default=False)

class PocketMoney(db.Model):
    __tablename__ = 'pocket_money'
    
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.id'), nullable=False)
    parent_id = db.Column(db.Integer, db.ForeignKey('parents.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    date_given = db.Column(db.Date, nullable=False)
    recurring = db.Column(db.Boolean, default=False)
    recurring_schedule = db.Column(db.String(50))  # 'weekly', 'monthly', etc.
    stored_in = db.Column(db.String(100))  # 'wallet', 'bank_account', etc.
    
class PocketMoneyLog(db.Model):
    __tablename__ = 'pocket_money_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    date = db.Column(db.Date, nullable=False)
    source = db.Column(db.String(100))  # 'allowance', 'chores', 'gift', etc.
    destination = db.Column(db.String(100))  # 'spent', 'saved', 'donated', etc.

class PocketMoneyPlace(db.Model):
    __tablename__ = 'pocket_money_places'
    
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)  # 'piggy_bank', 'savings_account', etc.
    amount_stored = db.Column(db.Numeric(10, 2), default=0.00)

class Goal(db.Model):
    __tablename__ = 'goals'
    
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    deadline = db.Column(db.Date)
    status = db.Column(db.String(20), default='active')  # 'active', 'completed', 'cancelled', 'waiting for approval'

class Spending(db.Model):
    __tablename__ = 'spendings'
    
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.id'), nullable=False)
    category = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    spend_date = db.Column(db.Date, nullable=False)
    description = db.Column(db.Text)

class Challenge(db.Model):
    __tablename__ = 'challenges'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    reward = db.Column(db.String(200))
    created_on = db.Column(db.DateTime, default=datetime.utcnow)
    ends_on = db.Column(db.DateTime)
    
    # Relationships
    progress = db.relationship('ChallengeProgress', backref='challenge', lazy=True)

class ChallengeProgress(db.Model):
    __tablename__ = 'challenge_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    child_id = db.Column(db.Integer, db.ForeignKey('children.id'), nullable=False)
    challenge_id = db.Column(db.Integer, db.ForeignKey('challenges.id'), nullable=False)
    status = db.Column(db.String(20), default='started')  # 'started', 'completed', 'abandoned'

class NotesEncouragement(db.Model):
    __tablename__ = 'notes_encouragement'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    child_id = db.Column(db.Integer, db.ForeignKey('children.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    date_sent = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    sender = db.relationship('User', backref='sent_notes', lazy=True)

class LlmChats(db.Model):
    __tablename__ = 'llm_chats'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message_id = db.Column(db.Integer, db.ForeignKey('challenges.id'), nullable=False)
    time = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    sender = db.relationship('User', backref='sent_chats', lazy=True)