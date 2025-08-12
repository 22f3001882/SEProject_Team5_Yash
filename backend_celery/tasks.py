from celery import shared_task
from datetime import datetime, timedelta, date
from backend_celery.mail_service import send_notification_email
from backend_celery.email_templates import (
    get_daily_reminder_template,
    get_weekly_reminder_template,
    get_parent_summary_template,
    get_allowance_notification_template,
    get_goal_achievement_template,
    get_low_balance_warning_template
)
from flask import current_app, render_template_string
from sqlalchemy import func, desc
from models import (
    Child, Parent, User, Goal, Spending, PocketMoney, 
    PocketMoneyPlace, PocketMoneyLog, ParentChildLink, db
)
import pytz
import calendar
from decimal import Decimal
@shared_task(ignore_result=True)
def send_daily_spending_reminders():
    """
    Send daily reminders to children to record their spending
    User Story 2.4: Daily reminders for spending updates
    """
    try:
        # Get all active children
        children = Child.query.join(User).filter(User.active == True).all()
        
        if not children:
            current_app.logger.info("No active children found for daily reminders")
            return
        
        sent_count = 0
        failed_count = 0
        
        for child in children:
            try:
                if not child.user_account or not child.user_account.email:
                    continue
                
                # Check if child has recorded spending today
                today = date.today()
                today_spending = Spending.query.filter(
                    Spending.child_id == child.id,
                    Spending.spend_date == today
                ).count()
                
                # Only send reminder if no spending recorded today
                if today_spending == 0:
                    template_content = get_daily_reminder_template(
                        child.user_account.name,
                        float(child.total_balance)
                    )
                    
                    if send_notification_email(
                        child.user_account.email,
                        "💰 Daily Spending Reminder",
                        template_content
                    ):
                        sent_count += 1
                    else:
                        failed_count += 1
                        
            except Exception as e:
                failed_count += 1
                current_app.logger.error(f"Failed to send daily reminder to child {child.id}: {str(e)}")
        
        current_app.logger.info(f"Daily reminders sent: {sent_count} successful, {failed_count} failed")
        
    except Exception as e:
        current_app.logger.error(f"Error in send_daily_spending_reminders: {str(e)}")

@shared_task(ignore_result=True)
def send_weekly_spending_reminders():
    """
    Send weekly reminders to children who haven't been tracking regularly
    User Story 2.4: Weekly reminders for spending updates
    """
    try:
        # Get all active children
        children = Child.query.join(User).filter(User.active == True).all()
        
        if not children:
            current_app.logger.info("No active children found for weekly reminders")
            return
        
        # Calculate date range for the past week
        today = date.today()
        week_ago = today - timedelta(days=7)
        
        sent_count = 0
        failed_count = 0
        
        for child in children:
            try:
                if not child.user_account or not child.user_account.email:
                    continue
                
                # Count spending entries in the past week
                week_spending_count = Spending.query.filter(
                    Spending.child_id == child.id,
                    Spending.spend_date >= week_ago,
                    Spending.spend_date <= today
                ).count()
                
                # Get total amount spent this week
                week_total = db.session.query(func.sum(Spending.amount)).filter(
                    Spending.child_id == child.id,
                    Spending.spend_date >= week_ago,
                    Spending.spend_date <= today
                ).scalar() or 0

                # Prepare week statistics
                week_stats = {
                    'entries_count': week_spending_count,
                    'total_spent': float(week_total),
                    'current_balance': float(child.total_balance),
                    'avg_per_entry': float(week_total) / week_spending_count if week_spending_count > 0 else 0
                }

                # Get active goals with progress
                active_goals = Goal.query.filter_by(
                    child_id=child.id, 
                    status='active'
                ).all()

                goals_data = []
                for goal in active_goals:
                    progress = (float(child.total_balance) / float(goal.amount)) * 100 if goal.amount > 0 else 0
                    remaining = max(0, float(goal.amount) - float(child.total_balance))
                    goals_data.append({
                        'title': goal.title,
                        'progress': progress,
                        'remaining': remaining
                    })

                template_content = get_weekly_reminder_template(
                    child.user_account.name,
                    week_stats,
                    goals_data
                )
                
                if send_notification_email(
                    child.user_account.email,
                    f"📊 Weekly Financial Summary - {today.strftime('%B %d, %Y')}",
                    template_content
                ):
                    sent_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                failed_count += 1
                current_app.logger.error(f"Failed to send weekly reminder to child {child.id}: {str(e)}")
        
        current_app.logger.info(f"Weekly reminders sent: {sent_count} successful, {failed_count} failed")
        
    except Exception as e:
        current_app.logger.error(f"Error in send_weekly_spending_reminders: {str(e)}")

@shared_task(ignore_result=True)
def send_weekly_parent_summaries():
    """
    Send weekly summaries to parents about their children's financial activity
    User Story 2.7: Weekly email summaries for parents
    """
    try:
        # Get all active parents
        parents = Parent.query.join(User).filter(User.active == True).all()
        
        if not parents:
            current_app.logger.info("No active parents found for weekly summaries")
            return
        
        # Calculate date range for the past week
        today = date.today()
        week_ago = today - timedelta(days=7)
        
        sent_count = 0
        failed_count = 0
        
        for parent in parents:
            try:
                if not parent.user_account or not parent.user_account.email:
                    continue
                
                # Get all children linked to this parent
                children_links = ParentChildLink.query.filter_by(parent_id=parent.id).all()
                
                if not children_links:
                    continue
                
                # Prepare family statistics
                total_family_balance = 0
                total_family_spent = 0
                total_family_allowances = 0
                children_data = []
                
                for link in children_links:
                    child = link.child
                    if not child:
                        continue
                    
                    # Get child's week statistics
                    week_spending = Spending.query.filter(
                        Spending.child_id == child.id,
                        Spending.spend_date >= week_ago,
                        Spending.spend_date <= today
                    ).all()
                    
                    week_total = sum(float(spend.amount) for spend in week_spending)
                    total_family_spent += week_total
                    total_family_balance += Decimal(str(child.total_balance))
                    
                    # Get allowances given this week
                    week_allowances = PocketMoney.query.filter(
                        PocketMoney.child_id == child.id,
                        PocketMoney.date_given >= week_ago,
                        PocketMoney.date_given <= today
                    ).all()
                    
                    week_allowance_total = sum(float(allowance.amount) for allowance in week_allowances)
                    total_family_allowances += week_allowance_total
                    
                    # Get spending breakdown by category
                    spending_by_category = {}
                    for spend in week_spending:
                        category = spend.category or 'Other'
                        spending_by_category[category] = spending_by_category.get(category, 0) + float(spend.amount)
                    
                    # Get goal progress
                    active_goals = Goal.query.filter_by(
                        child_id=child.id, 
                        status='active'
                    ).all()
                    
                    goals_data = []
                    for goal in active_goals:
                        progress = (float(child.total_balance) / float(goal.amount)) * 100 if goal.amount > 0 else 0
                        goals_data.append({
                            'title': goal.title,
                            'progress': progress
                        })
                    
                    child_data = {
                        'name': child.user_account.name if child.user_account else 'Unknown',
                        'balance': float(child.total_balance),
                        'week_spent': week_total,
                        'transaction_count': len(week_spending),
                        'allowances_received': week_allowance_total,
                        'spending_categories': spending_by_category,
                        'goals': goals_data
                    }
                    children_data.append(child_data)

                family_stats = {
                    'total_balance': total_family_balance,
                    'total_spent': total_family_spent,
                    'total_allowances': total_family_allowances,
                    'children_count': len(children_links)
                }

                template_content = get_parent_summary_template(
                    parent.user_account.name,
                    children_data,
                    family_stats
                )
                
                if send_notification_email(
                    parent.user_account.email,
                    f"👨‍👩‍👧‍👦 Weekly Family Financial Summary - {today.strftime('%B %d, %Y')}",
                    template_content
                ):
                    sent_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                failed_count += 1
                current_app.logger.error(f"Failed to send weekly summary to parent {parent.id}: {str(e)}")
        
        current_app.logger.info(f"Weekly parent summaries sent: {sent_count} successful, {failed_count} failed")
        
    except Exception as e:
        current_app.logger.error(f"Error in send_weekly_parent_summaries: {str(e)}")

@shared_task(ignore_result=True)
def process_recurring_allowances():
    """
    Process and distribute recurring allowances based on schedule
    """
    try:
        today = date.today()

        # Only get active recurring allowances
        recurring_allowances = PocketMoney.query.filter_by(recurring=True).all()

        if not recurring_allowances:
            current_app.logger.info("No recurring allowances found")
            return

        processed_count = 0
        failed_count = 0

        for allowance in recurring_allowances:
            try:
                if not allowance.recurring_schedule:
                    continue

                # Check if allowance should be processed today
                should_process = False
                days_since = (today - allowance.date_given).days

                if allowance.recurring_schedule == 'daily':
                    should_process = True
                elif allowance.recurring_schedule == 'weekly':
                    should_process = days_since >= 7
                elif allowance.recurring_schedule == 'fortnightly':
                    should_process = days_since >= 14
                elif allowance.recurring_schedule == 'monthly':
                    should_process = (
                        today.month != allowance.date_given.month or
                        today.year != allowance.date_given.year
                    )

                if not should_process:
                    continue

                # Create new allowance entry
                new_allowance = PocketMoney(
                    child_id=allowance.child_id,
                    parent_id=allowance.parent_id,
                    amount=allowance.amount,
                    date_given=today,
                    recurring=True,
                    recurring_schedule=allowance.recurring_schedule,
                    stored_in=allowance.stored_in
                )

                # Mark the old one as processed so it won't run again
                allowance.recurring = False

                # Update child's balance (Decimal safe)
                child = Child.query.get(allowance.child_id)
                if child:
                    child.total_balance += Decimal(str(allowance.amount))

                    # Update money storage place if specified
                    if allowance.stored_in:
                        money_place = PocketMoneyPlace.query.filter_by(
                            child_id=child.id,
                            name=allowance.stored_in
                        ).first()
                        if money_place:
                            money_place.amount_stored += Decimal(str(allowance.amount))

                    # Create transaction log
                    log_entry = PocketMoneyLog(
                        child_id=child.id,
                        amount=allowance.amount,
                        date=today,
                        source='Recurring Allowance',
                        destination=allowance.stored_in or 'General Balance'
                    )

                    db.session.add(new_allowance)
                    db.session.add(log_entry)

                    # Send notification
                    if child.user_account and child.user_account.email:
                        parent_name = (
                            allowance.parent.user_account.name
                            if allowance.parent and allowance.parent.user_account
                            else "Your parent"
                        )
                        template_content = get_allowance_notification_template(
                            child.user_account.name,
                            float(allowance.amount),
                            allowance.recurring_schedule,
                            parent_name,
                            float(child.total_balance),
                            allowance.stored_in
                        )
                        send_notification_email(
                            child.user_account.email,
                            f"💰 {allowance.recurring_schedule.title()} Allowance Received!",
                            template_content
                        )

                    processed_count += 1

                # Update original's date_given (optional)
                allowance.date_given = today

            except Exception as e:
                failed_count += 1
                current_app.logger.error(f"Failed to process recurring allowance {allowance.id}: {str(e)}")
                db.session.rollback()
                continue

        if processed_count > 0:
            db.session.commit()

        current_app.logger.info(f"Recurring allowances processed: {processed_count} successful, {failed_count} failed")

    except Exception as e:
        current_app.logger.error(f"Error in process_recurring_allowances: {str(e)}")
        db.session.rollback()

@shared_task(ignore_result=False, bind=True)
def create_child_financial_report(self, child_id, start_date, end_date):
    """
    Generate comprehensive financial report for a child
    Can be used by parents to get detailed analysis
    """
    try:
        child = Child.query.get(child_id)
        if not child:
            return {'error': 'Child not found'}
        
        start_dt = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_dt = datetime.strptime(end_date, '%Y-%m-%d').date()
        
        # Get spending data
        spending_records = Spending.query.filter(
            Spending.child_id == child_id,
            Spending.spend_date >= start_dt,
            Spending.spend_date <= end_dt
        ).all()
        
        # Get allowance data
        allowances = PocketMoney.query.filter(
            PocketMoney.child_id == child_id,
            PocketMoney.date_given >= start_dt,
            PocketMoney.date_given <= end_dt
        ).all()
        
        # Analyze data
        total_spent = sum(float(spend.amount) for spend in spending_records)
        total_received = sum(float(allowance.amount) for allowance in allowances)
        
        # Spending by category
        spending_by_category = {}
        for spend in spending_records:
            category = spend.category or 'Other'
            spending_by_category[category] = spending_by_category.get(category, 0) + float(spend.amount)
        
        # Goals progress
        goals = Goal.query.filter_by(child_id=child_id).all()
        goals_data = []
        for goal in goals:
            progress = (float(child.total_balance) / float(goal.amount)) * 100 if goal.amount > 0 else 0
            goals_data.append({
                'title': goal.title,
                'target': float(goal.amount),
                'progress': progress,
                'status': goal.status
            })
        
        report_data = {
            'child_name': child.user_account.name if child.user_account else 'Unknown',
            'report_period': f"{start_date} to {end_date}",
            'current_balance': float(child.total_balance),
            'total_spent': total_spent,
            'total_received': total_received,
            'net_change': total_received - total_spent,
            'spending_by_category': spending_by_category,
            'goals': goals_data,
            'transaction_count': len(spending_records),
            'allowance_count': len(allowances)
        }
        
        return report_data
        
    except Exception as e:
        current_app.logger.error(f"Error creating financial report for child {child_id}: {str(e)}")
        return {'error': str(e)}