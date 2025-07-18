from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from datetime import datetime, date, timedelta
import random
from decimal import Decimal

# Import your existing models (assuming they're in the same file or properly imported)

from models import *

def create_dummy_data():
    """Create comprehensive dummy data for the school management system"""
    
    # Clear existing data (optional - uncomment if you want to start fresh)
    db.drop_all()
    db.create_all()
    
    print("Creating dummy data...")
    
    # 1. Create Admin Users
    admin_users = [
        {
            'name': 'John Administrator',
            'email': 'admin@school.com',
            'password': generate_password_hash('admin123'),
            'role': 'admin'
        },
        {
            'name': 'Sarah Manager',
            'email': 'sarah.manager@school.com',
            'password': generate_password_hash('manager123'),
            'role': 'admin'
        }
    ]
    
    admin_objects = []
    for admin_data in admin_users:
        admin = User(**admin_data)
        db.session.add(admin)
        admin_objects.append(admin)
    
    db.session.commit()
    print(f"Created {len(admin_objects)} admin users")
    
    # 2. Create Schools
    schools_data = [
        {
            'name': 'Greenwood Elementary School',
            'address': '123 Oak Street, Springfield, IL 62701',
            'user_id': admin_objects[0].id
        },
        {
            'name': 'Riverside Middle School',
            'address': '456 River Road, Springfield, IL 62702',
            'user_id': admin_objects[1].id
        }
    ]
    
    school_objects = []
    for school_data in schools_data:
        school = School(**school_data)
        db.session.add(school)
        school_objects.append(school)
    
    db.session.commit()
    print(f"Created {len(school_objects)} schools")
    
    # 3. Create Teacher Users and Teacher records
    teacher_users_data = [
        {'name': 'Emily Johnson', 'email': 'emily.johnson@school.com', 'role': 'teacher'},
        {'name': 'Michael Brown', 'email': 'michael.brown@school.com', 'role': 'teacher'},
        {'name': 'Lisa Davis', 'email': 'lisa.davis@school.com', 'role': 'teacher'},
        {'name': 'Robert Wilson', 'email': 'robert.wilson@school.com', 'role': 'teacher'},
        {'name': 'Jennifer Garcia', 'email': 'jennifer.garcia@school.com', 'role': 'teacher'},
        {'name': 'David Miller', 'email': 'david.miller@school.com', 'role': 'teacher'}
    ]
    
    teacher_user_objects = []
    for teacher_data in teacher_users_data:
        teacher_data['password'] = generate_password_hash('teacher123')
        teacher_user = User(**teacher_data)
        db.session.add(teacher_user)
        teacher_user_objects.append(teacher_user)
    
    db.session.commit()
    
    # Create Teacher records
    teacher_objects = []
    for i, teacher_user in enumerate(teacher_user_objects):
        teacher = Teacher(
            user_id=teacher_user.id,
            school_id=school_objects[i % len(school_objects)].id
        )
        db.session.add(teacher)
        teacher_objects.append(teacher)
    
    db.session.commit()
    print(f"Created {len(teacher_objects)} teachers")
    
    # 4. Create Classes
    classes_data = [
        {'name': '1st Grade A', 'teacher_id': teacher_objects[0].id, 'school_id': school_objects[0].id},
        {'name': '1st Grade B', 'teacher_id': teacher_objects[1].id, 'school_id': school_objects[0].id},
        {'name': '2nd Grade A', 'teacher_id': teacher_objects[2].id, 'school_id': school_objects[0].id},
        {'name': '6th Grade A', 'teacher_id': teacher_objects[3].id, 'school_id': school_objects[1].id},
        {'name': '7th Grade A', 'teacher_id': teacher_objects[4].id, 'school_id': school_objects[1].id},
        {'name': '8th Grade A', 'teacher_id': teacher_objects[5].id, 'school_id': school_objects[1].id}
    ]
    
    class_objects = []
    for class_data in classes_data:
        class_obj = Class(**class_data)
        db.session.add(class_obj)
        class_objects.append(class_obj)
    
    db.session.commit()
    print(f"Created {len(class_objects)} classes")
    
    # 5. Create Parent Users and Parent records
    parent_users_data = [
        {'name': 'Mark Thompson', 'email': 'mark.thompson@email.com', 'role': 'parent'},
        {'name': 'Susan Thompson', 'email': 'susan.thompson@email.com', 'role': 'parent'},
        {'name': 'James Rodriguez', 'email': 'james.rodriguez@email.com', 'role': 'parent'},
        {'name': 'Maria Rodriguez', 'email': 'maria.rodriguez@email.com', 'role': 'parent'},
        {'name': 'Tom Anderson', 'email': 'tom.anderson@email.com', 'role': 'parent'},
        {'name': 'Rachel Anderson', 'email': 'rachel.anderson@email.com', 'role': 'parent'},
        {'name': 'Kevin Lee', 'email': 'kevin.lee@email.com', 'role': 'parent'},
        {'name': 'Amy Lee', 'email': 'amy.lee@email.com', 'role': 'parent'},
        {'name': 'Steve Martin', 'email': 'steve.martin@email.com', 'role': 'parent'},
        {'name': 'Linda Martin', 'email': 'linda.martin@email.com', 'role': 'parent'}
    ]
    
    parent_user_objects = []
    for parent_data in parent_users_data:
        parent_data['password'] = generate_password_hash('parent123')
        parent_user = User(**parent_data)
        db.session.add(parent_user)
        parent_user_objects.append(parent_user)
    
    db.session.commit()
    
    # Create Parent records
    parent_objects = []
    for parent_user in parent_user_objects:
        parent = Parent(user_id=parent_user.id)
        db.session.add(parent)
        parent_objects.append(parent)
    
    db.session.commit()
    print(f"Created {len(parent_objects)} parents")
    
    # 6. Create Child Users and Child records
    child_users_data = [
        {'name': 'Emma Thompson', 'email': 'emma.thompson@email.com', 'role': 'child'},
        {'name': 'Liam Thompson', 'email': 'liam.thompson@email.com', 'role': 'child'},
        {'name': 'Sofia Rodriguez', 'email': 'sofia.rodriguez@email.com', 'role': 'child'},
        {'name': 'Noah Anderson', 'email': 'noah.anderson@email.com', 'role': 'child'},
        {'name': 'Olivia Anderson', 'email': 'olivia.anderson@email.com', 'role': 'child'},
        {'name': 'Ethan Lee', 'email': 'ethan.lee@email.com', 'role': 'child'},
        {'name': 'Ava Lee', 'email': 'ava.lee@email.com', 'role': 'child'},
        {'name': 'Mason Martin', 'email': 'mason.martin@email.com', 'role': 'child'},
        {'name': 'Isabella Martin', 'email': 'isabella.martin@email.com', 'role': 'child'}
    ]
    
    child_user_objects = []
    for child_data in child_users_data:
        child_data['password'] = generate_password_hash('child123')
        child_user = User(**child_data)
        db.session.add(child_user)
        child_user_objects.append(child_user)
    
    db.session.commit()
    
    # Create Child records
    child_objects = []
    for i, child_user in enumerate(child_user_objects):
        child = Child(
            user_id=child_user.id,
            class_id=class_objects[i % len(class_objects)].id,
            total_balance=Decimal(str(random.uniform(10, 100)))
        )
        db.session.add(child)
        child_objects.append(child)
    
    db.session.commit()
    print(f"Created {len(child_objects)} children")
    
    # 7. Create Parent-Child Links
    parent_child_links = [
        # Thompson family
        {'parent_id': parent_objects[0].id, 'child_id': child_objects[0].id, 'primary': True},
        {'parent_id': parent_objects[1].id, 'child_id': child_objects[0].id, 'primary': False},
        {'parent_id': parent_objects[0].id, 'child_id': child_objects[1].id, 'primary': True},
        {'parent_id': parent_objects[1].id, 'child_id': child_objects[1].id, 'primary': False},
        # Rodriguez family
        {'parent_id': parent_objects[2].id, 'child_id': child_objects[2].id, 'primary': True},
        {'parent_id': parent_objects[3].id, 'child_id': child_objects[2].id, 'primary': False},
        # Anderson family
        {'parent_id': parent_objects[4].id, 'child_id': child_objects[3].id, 'primary': True},
        {'parent_id': parent_objects[5].id, 'child_id': child_objects[3].id, 'primary': False},
        {'parent_id': parent_objects[4].id, 'child_id': child_objects[4].id, 'primary': True},
        {'parent_id': parent_objects[5].id, 'child_id': child_objects[4].id, 'primary': False},
        # Lee family
        {'parent_id': parent_objects[6].id, 'child_id': child_objects[5].id, 'primary': True},
        {'parent_id': parent_objects[7].id, 'child_id': child_objects[5].id, 'primary': False},
        {'parent_id': parent_objects[6].id, 'child_id': child_objects[6].id, 'primary': True},
        {'parent_id': parent_objects[7].id, 'child_id': child_objects[6].id, 'primary': False},
        # Martin family
        {'parent_id': parent_objects[8].id, 'child_id': child_objects[7].id, 'primary': True},
        {'parent_id': parent_objects[9].id, 'child_id': child_objects[7].id, 'primary': False},
        {'parent_id': parent_objects[8].id, 'child_id': child_objects[8].id, 'primary': True},
        {'parent_id': parent_objects[9].id, 'child_id': child_objects[8].id, 'primary': False}
    ]
    
    for link_data in parent_child_links:
        link = ParentChildLink(**link_data)
        db.session.add(link)
    
    db.session.commit()
    print(f"Created {len(parent_child_links)} parent-child links")
    
    # 8. Create Pocket Money records
    pocket_money_records = []
    for i, child in enumerate(child_objects):
        # Each child gets 2-3 pocket money records
        for j in range(random.randint(2, 3)):
            pocket_money = PocketMoney(
                child_id=child.id,
                parent_id=parent_objects[i * 2].id,  # Primary parent
                amount=Decimal(str(random.uniform(5, 25))),
                date_given=date.today() - timedelta(days=random.randint(1, 30)),
                recurring=random.choice([True, False]),
                recurring_schedule=random.choice(['weekly', 'monthly', None]),
                stored_in=random.choice(['wallet', 'piggy_bank', 'savings_account'])
            )
            db.session.add(pocket_money)
            pocket_money_records.append(pocket_money)
    
    db.session.commit()
    print(f"Created {len(pocket_money_records)} pocket money records")
    
    # 9. Create Pocket Money Logs
    pocket_money_logs = []
    for child in child_objects:
        for _ in range(random.randint(5, 10)):
            log = PocketMoneyLog(
                child_id=child.id,
                amount=Decimal(str(random.uniform(1, 20))),
                date=date.today() - timedelta(days=random.randint(1, 60)),
                source=random.choice(['allowance', 'chores', 'gift', 'birthday', 'good_grades']),
                destination=random.choice(['spent', 'saved', 'donated', 'invested'])
            )
            db.session.add(log)
            pocket_money_logs.append(log)
    
    db.session.commit()
    print(f"Created {len(pocket_money_logs)} pocket money logs")
    
    # 10. Create Pocket Money Places
    pocket_money_places = []
    for child in child_objects:
        places = ['piggy_bank', 'wallet', 'savings_account', 'jar']
        for place in random.sample(places, random.randint(2, 3)):
            pmp = PocketMoneyPlace(
                child_id=child.id,
                name=place,
                amount_stored=Decimal(str(random.uniform(5, 50)))
            )
            db.session.add(pmp)
            pocket_money_places.append(pmp)
    
    db.session.commit()
    print(f"Created {len(pocket_money_places)} pocket money places")
    
    # 11. Create Goals
    goals = []
    goal_titles = [
        'New Bicycle', 'Nintendo Switch', 'Art Supplies', 'Save for College',
        'New Books', 'Toy Robot', 'Skateboard', 'Video Game', 'Lego Set',
        'Musical Instrument', 'Sports Equipment', 'Tablet'
    ]
    
    for child in child_objects:
        for _ in range(random.randint(1, 3)):
            goal = Goal(
                child_id=child.id,
                title=random.choice(goal_titles),
                amount=Decimal(str(random.uniform(20, 200))),
                deadline=date.today() + timedelta(days=random.randint(30, 365)),
                status=random.choice(['active', 'completed', 'cancelled'])
            )
            db.session.add(goal)
            goals.append(goal)
    
    db.session.commit()
    print(f"Created {len(goals)} goals")
    
    # 12. Create Spendings
    spendings = []
    spending_categories = [
        'Toys', 'Candy', 'Books', 'Games', 'Clothes', 'Food', 'Electronics',
        'Sports', 'Art Supplies', 'Music', 'Movies', 'Gifts'
    ]
    
    for child in child_objects:
        for _ in range(random.randint(3, 8)):
            spending = Spending(
                child_id=child.id,
                category=random.choice(spending_categories),
                amount=Decimal(str(random.uniform(1, 25))),
                spend_date=date.today() - timedelta(days=random.randint(1, 30)),
                description=f"Bought {random.choice(['something cool', 'a nice item', 'a fun thing'])}"
            )
            db.session.add(spending)
            spendings.append(spending)
    
    db.session.commit()
    print(f"Created {len(spendings)} spending records")
    
    # 13. Create Challenges
    challenges_data = [
        {
            'title': 'Save $50 Challenge',
            'description': 'Save $50 in your piggy bank within 2 months',
            'reward': 'Extra $10 bonus',
            'ends_on': datetime.now() + timedelta(days=60)
        },
        {
            'title': 'Chores Champion',
            'description': 'Complete all your chores for 4 weeks straight',
            'reward': 'Choose a family movie night',
            'ends_on': datetime.now() + timedelta(days=28)
        },
        {
            'title': 'Reading Marathon',
            'description': 'Read 10 books this month',
            'reward': 'New book of your choice',
            'ends_on': datetime.now() + timedelta(days=30)
        },
        {
            'title': 'Healthy Eating Week',
            'description': 'Eat fruits and vegetables every day for a week',
            'reward': '$5 bonus allowance',
            'ends_on': datetime.now() + timedelta(days=7)
        }
    ]
    
    challenge_objects = []
    for challenge_data in challenges_data:
        challenge = Challenge(**challenge_data)
        db.session.add(challenge)
        challenge_objects.append(challenge)
    
    db.session.commit()
    print(f"Created {len(challenge_objects)} challenges")
    
    # 14. Create Challenge Progress
    challenge_progress = []
    for child in child_objects:
        # Each child participates in 1-3 challenges
        for challenge in random.sample(challenge_objects, random.randint(1, 3)):
            progress = ChallengeProgress(
                child_id=child.id,
                challenge_id=challenge.id,
                status=random.choice(['started', 'completed', 'abandoned'])
            )
            db.session.add(progress)
            challenge_progress.append(progress)
    
    db.session.commit()
    print(f"Created {len(challenge_progress)} challenge progress records")
    
    # 15. Create Notes of Encouragement
    notes = []
    encouragement_messages = [
        "Great job on saving money this week!",
        "I'm proud of how responsible you're being with your allowance.",
        "Keep up the good work with your chores!",
        "You're doing amazing with your savings goal!",
        "I noticed you've been very careful with your spending. Well done!",
        "Your hard work is paying off. Keep it up!",
        "You're learning so much about money management!",
        "I'm impressed by your dedication to your goals."
    ]
    
    # Parents and teachers send notes to children
    all_senders = parent_user_objects + teacher_user_objects
    
    for child in child_objects:
        for _ in range(random.randint(2, 5)):
            note = NotesEncouragement(
                sender_id=random.choice(all_senders).id,
                child_id=child.id,
                message=random.choice(encouragement_messages),
                date_sent=datetime.now() - timedelta(days=random.randint(1, 30))
            )
            db.session.add(note)
            notes.append(note)
    
    db.session.commit()
    print(f"Created {len(notes)} encouragement notes")
    
    print("\n=== DUMMY DATA CREATION COMPLETE ===")
    print(f"Total records created:")
    print(f"- Users: {len(admin_objects) + len(teacher_user_objects) + len(parent_user_objects) + len(child_user_objects)}")
    print(f"- Schools: {len(school_objects)}")
    print(f"- Teachers: {len(teacher_objects)}")
    print(f"- Classes: {len(class_objects)}")
    print(f"- Parents: {len(parent_objects)}")
    print(f"- Children: {len(child_objects)}")
    print(f"- Parent-Child Links: {len(parent_child_links)}")
    print(f"- Pocket Money Records: {len(pocket_money_records)}")
    print(f"- Pocket Money Logs: {len(pocket_money_logs)}")
    print(f"- Pocket Money Places: {len(pocket_money_places)}")
    print(f"- Goals: {len(goals)}")
    print(f"- Spendings: {len(spendings)}")
    print(f"- Challenges: {len(challenge_objects)}")
    print(f"- Challenge Progress: {len(challenge_progress)}")
    print(f"- Encouragement Notes: {len(notes)}")
    
    print("\n=== LOGIN CREDENTIALS ===")
    print("Admins:")
    print("- admin@school.com / admin123")
    print("- sarah.manager@school.com / manager123")
    print("\nTeachers:")
    for teacher in teacher_users_data:
        print(f"- {teacher['email']} / teacher123")
    print("\nParents:")
    for parent in parent_users_data:
        print(f"- {parent['email']} / parent123")
    print("\nChildren:")
    for child in child_users_data:
        print(f"- {child['email']} / child123")

if __name__ == "__main__":
    # Make sure to run this with your Flask app context
    with app.app_context():
        create_dummy_data()