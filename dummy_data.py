"""
Script to load dummy data for testing the child financial management system
"""

from app import app
from models import *
from flask_security import hash_password
from datetime import datetime, date, timedelta
import random

def clear_data():
    """Clear existing data"""
    print("Clearing existing data...")
    
    # Clear in reverse order of dependencies
    ChallengeProgress.query.delete()
    Challenge.query.delete()
    NotesEncouragement.query.delete()
    Spending.query.delete()
    Goal.query.delete()
    PocketMoneyLog.query.delete()
    PocketMoneyPlace.query.delete()
    PocketMoney.query.delete()
    ParentChildLink.query.delete()
    Child.query.delete()
    Parent.query.delete()
    Teacher.query.delete()
    Class.query.delete()
    School.query.delete()
    UserRoles.query.delete()
    User.query.delete()
    Role.query.delete()
    
    db.session.commit()
    print("Data cleared!")

def create_roles():
    """Create basic roles"""
    print("Creating roles...")
    
    roles = [
        {'name': 'admin', 'description': 'Administrator'},
        {'name': 'child', 'description': 'Child user'},
        {'name': 'parent', 'description': 'Parent user'},
        {'name': 'teacher', 'description': 'Teacher user'},
        {'name': 'school', 'description': 'School administrator'}
    ]
    
    for role_data in roles:
        role = Role(name=role_data['name'], description=role_data['description'])
        db.session.add(role)
    
    db.session.commit()
    print("Roles created!")

def create_schools_and_classes():
    """Create dummy schools and classes"""
    print("Creating schools and classes...")
    
    # Create school admin user
    school_user = User(
        email='greenwood@school.com',
        password=hash_password('password123'),
        name='Greenwood Elementary',
        fs_uniquifier='school1',
        active=True
    )
    db.session.add(school_user)
    db.session.flush()
    
    # Assign school role
    school_role = Role.query.filter_by(name='school').first()
    user_role = UserRoles(user_id=school_user.id, role_id=school_role.id)
    db.session.add(user_role)
    
    # Create school
    school = School(
        name='Greenwood Elementary School',
        address='123 Education Street, Learning City',
        user_id=school_user.id
    )
    db.session.add(school)
    db.session.flush()
    
    # Create teacher user
    teacher_user = User(
        email='ms.johnson@school.com',
        password=hash_password('password123'),
        name='Ms. Sarah Johnson',
        fs_uniquifier='teacher1',
        active=True
    )
    db.session.add(teacher_user)
    db.session.flush()
    
    # Assign teacher role
    teacher_role = Role.query.filter_by(name='teacher').first()
    user_role = UserRoles(user_id=teacher_user.id, role_id=teacher_role.id)
    db.session.add(user_role)
    
    # Create teacher
    teacher = Teacher(
        user_id=teacher_user.id,
        school_id=school.id
    )
    db.session.add(teacher)
    db.session.flush()
    
    # Create class
    class_obj = Class(
        name='Grade 5A',
        teacher_id=teacher.id,
        school_id=school.id
    )
    db.session.add(class_obj)
    db.session.commit()
    
    print("Schools and classes created!")
    return class_obj.id

def create_parents():
    """Create dummy parents"""
    print("Creating parents...")
    
    parents_data = [
        {'email': 'john.smith@email.com', 'name': 'John Smith'},
        {'email': 'mary.doe@email.com', 'name': 'Mary Doe'},
        {'email': 'david.brown@email.com', 'name': 'David Brown'},
        {'email': 'lisa.wilson@email.com', 'name': 'Lisa Wilson'},
    ]
    
    parent_ids = []
    parent_role = Role.query.filter_by(name='parent').first()
    
    for i, parent_data in enumerate(parents_data):
        # Create user
        user = User(
            email=parent_data['email'],
            password=hash_password('password123'),
            name=parent_data['name'],
            fs_uniquifier=f'parent{i+1}',
            active=True
        )
        db.session.add(user)
        db.session.flush()
        
        # Assign role
        user_role = UserRoles(user_id=user.id, role_id=parent_role.id)
        db.session.add(user_role)
        
        # Create parent profile
        parent = Parent(user_id=user.id)
        db.session.add(parent)
        db.session.flush()
        
        parent_ids.append(parent.id)
    
    db.session.commit()
    print("Parents created!")
    return parent_ids

def create_children(class_id, parent_ids):
    """Create dummy children"""
    print("Creating children...")
    
    children_data = [
        {'email': 'alex.smith@email.com', 'name': 'Alex Smith', 'balance': 45.50},
        {'email': 'emma.doe@email.com', 'name': 'Emma Doe', 'balance': 32.75},
        {'email': 'noah.brown@email.com', 'name': 'Noah Brown', 'balance': 18.25},
        {'email': 'sophie.wilson@email.com', 'name': 'Sophie Wilson', 'balance': 67.00},
    ]
    
    child_ids = []
    child_role = Role.query.filter_by(name='child').first()
    
    for i, child_data in enumerate(children_data):
        # Create user
        user = User(
            email=child_data['email'],
            password=hash_password('password123'),
            name=child_data['name'],
            fs_uniquifier=f'child{i+1}',
            active=True
        )
        db.session.add(user)
        db.session.flush()
        
        # Assign role
        user_role = UserRoles(user_id=user.id, role_id=child_role.id)
        db.session.add(user_role)
        
        # Create child profile
        child = Child(
            user_id=user.id,
            class_id=class_id,
            total_balance=child_data['balance']
        )
        db.session.add(child)
        db.session.flush()
        
        child_ids.append(child.id)
        
        # Link to parent
        if i < len(parent_ids):
            parent_link = ParentChildLink(
                parent_id=parent_ids[i],
                child_id=child.id,
                primary=True
            )
            db.session.add(parent_link)
    
    db.session.commit()
    print("Children created!")
    return child_ids

def create_goals(child_ids):
    """Create dummy goals"""
    print("Creating goals...")
    
    goals_data = [
        {'title': 'New Bicycle', 'amount': 150.00, 'days_ahead': 30},
        {'title': 'Video Game', 'amount': 60.00, 'days_ahead': 15},
        {'title': 'Art Supplies', 'amount': 25.00, 'days_ahead': 10},
        {'title': 'School Trip', 'amount': 45.00, 'days_ahead': 20},
        {'title': 'Birthday Gift for Mom', 'amount': 30.00, 'days_ahead': 25},
    ]
    
    for child_id in child_ids:
        # Create 1-2 goals per child
        num_goals = random.randint(1, 2)
        selected_goals = random.sample(goals_data, num_goals)
        
        for goal_data in selected_goals:
            goal = Goal(
                child_id=child_id,
                title=goal_data['title'],
                amount=goal_data['amount'],
                deadline=date.today() + timedelta(days=goal_data['days_ahead']),
                status='active'
            )
            db.session.add(goal)
    
    db.session.commit()
    print("Goals created!")

def create_spending_records(child_ids):
    """Create dummy spending records"""
    print("Creating spending records...")
    
    categories = ['Food & Drinks', 'Toys & Games', 'Books', 'Clothes', 'Entertainment', 'Other']
    
    for child_id in child_ids:
        # Create 3-8 spending records per child
        num_records = random.randint(3, 8)
        
        for _ in range(num_records):
            spend_date = date.today() - timedelta(days=random.randint(1, 30))
            amount = round(random.uniform(2.50, 15.00), 2)
            category = random.choice(categories)
            
            descriptions = {
                'Food & Drinks': ['Snack at school', 'Ice cream', 'Juice box', 'Candy'],
                'Toys & Games': ['Small toy', 'Trading cards', 'Puzzle', 'Ball'],
                'Books': ['Comic book', 'Storybook', 'Magazine', 'Notebook'],
                'Clothes': ['Socks', 'Hair accessory', 'Stickers', 'Badge'],
                'Entertainment': ['Movie ticket', 'Arcade game', 'Mini golf', 'Bowling'],
                'Other': ['Gift for friend', 'Charity donation', 'School supplies', 'Miscellaneous']
            }
            
            description = random.choice(descriptions[category])
            
            spending = Spending(
                child_id=child_id,
                category=category,
                amount=amount,
                spend_date=spend_date,
                description=description
            )
            db.session.add(spending)
    
    db.session.commit()
    print("Spending records created!")

def create_money_places(child_ids):
    """Create dummy money storage places"""
    print("Creating money storage places...")
    
    place_names = ['Piggy Bank', 'Wallet', 'Savings Jar', 'Bank Account', 'Secret Box']
    
    for child_id in child_ids:
        # Create 2-3 money places per child
        num_places = random.randint(2, 3)
        selected_places = random.sample(place_names, num_places)
        
        child = Child.query.get(child_id)
        total_balance = float(child.total_balance)
        
        for i, place_name in enumerate(selected_places):
            # Distribute balance across places
            if i == len(selected_places) - 1:
                # Last place gets remaining balance
                amount = total_balance
            else:
                # Random portion of remaining balance
                max_amount = total_balance * 0.6
                amount = round(random.uniform(0, max_amount), 2)
                total_balance -= amount
            
            place = PocketMoneyPlace(
                child_id=child_id,
                name=place_name,
                amount_stored=amount
            )
            db.session.add(place)
    
    db.session.commit()
    print("Money storage places created!")

def create_challenges():
    """Create dummy challenges"""
    print("Creating challenges...")
    
    challenges_data = [
        {
            'title': 'Save $10 This Week',
            'description': 'Try to save at least $10 by the end of this week!',
            'reward': 'Extra $2 bonus',
            'days_ahead': 7
        },
        {
            'title': 'Track Every Spend',
            'description': 'Record every single purchase you make for one week.',
            'reward': 'Financial tracking badge',
            'days_ahead': 14
        },
        {
            'title': 'Compare Prices',
            'description': 'Before buying something, find and compare prices from 3 different places.',
            'reward': 'Smart shopper certificate',
            'days_ahead': 21
        },
        {
            'title': 'Help with Chores',
            'description': 'Complete 5 extra chores to earn additional pocket money.',
            'reward': '$5 bonus',
            'days_ahead': 10
        }
    ]
    
    for challenge_data in challenges_data:
        challenge = Challenge(
            title=challenge_data['title'],
            description=challenge_data['description'],
            reward=challenge_data['reward'],
            created_on=datetime.now(),
            ends_on=datetime.now() + timedelta(days=challenge_data['days_ahead'])
        )
        db.session.add(challenge)
    
    db.session.commit()
    print("Challenges created!")

def create_pocket_money_logs(child_ids, parent_ids):
    """Create dummy pocket money logs"""
    print("Creating pocket money logs...")
    
    sources = ['Weekly allowance', 'Chores', 'Birthday gift', 'Good grades bonus', 'Extra help']
    destinations = ['Piggy Bank', 'Wallet', 'Savings Account', 'Spending money']
    
    for child_id in child_ids:
        # Create 2-5 pocket money logs per child
        num_logs = random.randint(2, 5)
        
        for _ in range(num_logs):
            log_date = date.today() - timedelta(days=random.randint(1, 30))
            amount = round(random.uniform(5.00, 25.00), 2)
            
            log = PocketMoneyLog(
                child_id=child_id,
                amount=amount,
                date=log_date,
                source=random.choice(sources),
                destination=random.choice(destinations)
            )
            db.session.add(log)
    
    db.session.commit()
    print("Pocket money logs created!")

def main():
    """Main function to load all dummy data"""
    with app.app_context():
        print("Starting dummy data loading...")
        
        # Clear existing data
        clear_data()
        
        # Create base data
        create_roles()
        class_id = create_schools_and_classes()
        parent_ids = create_parents()
        child_ids = create_children(class_id, parent_ids)
        
        # Create child-related data
        create_goals(child_ids)
        create_spending_records(child_ids)
        create_money_places(child_ids)
        create_challenges()
        create_pocket_money_logs(child_ids, parent_ids)
        
        print("\n" + "="*50)
        print("DUMMY DATA LOADED SUCCESSFULLY!")
        print("="*50)
        print("\nTest Login Credentials:")
        print("\nChildren:")
        print("  alex.smith@email.com / password123")
        print("  emma.doe@email.com / password123")
        print("  noah.brown@email.com / password123")
        print("  sophie.wilson@email.com / password123")
        print("\nParents:")
        print("  john.smith@email.com / password123")
        print("  mary.doe@email.com / password123")
        print("  david.brown@email.com / password123")
        print("  lisa.wilson@email.com / password123")
        print("\nTeacher:")
        print("  ms.johnson@school.com / password123")
        print("\nSchool:")
        print("  greenwood@school.com / password123")
        print("\n" + "="*50)

if __name__ == '__main__':
    main()
