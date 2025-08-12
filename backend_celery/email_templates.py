"""
Email template management for Kids Pocket Money Tracker
Provides consistent HTML templates for different types of notifications
"""

def get_base_template(content: str, title: str = "Kids Pocket Money Tracker") -> str:
    """
    Base HTML template for all emails
    
    Args:
        content: The main content to insert into the template
        title: Email title for the header
    
    Returns:
        Complete HTML email template
    """
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{title}</title>
        <style>
            body {{ 
                font-family: 'Arial', sans-serif; 
                line-height: 1.6; 
                color: #333; 
                margin: 0; 
                padding: 0;
                background-color: #f4f4f4;
            }}
            .email-container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: white;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .header {{ 
                background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                color: white; 
                padding: 20px; 
                text-align: center;
                border-radius: 8px 8px 0 0;
            }}
            .header h2 {{
                margin: 0;
                font-size: 24px;
                font-weight: 300;
            }}
            .content {{ 
                padding: 30px; 
                background-color: white;
            }}
            .footer {{ 
                background-color: #333; 
                color: white; 
                padding: 15px; 
                text-align: center; 
                font-size: 12px;
                border-radius: 0 0 8px 8px;
            }}
            .highlight {{ 
                background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                padding: 20px; 
                border-radius: 8px; 
                margin: 15px 0;
                border-left: 4px solid #4CAF50;
            }}
            .balance {{ 
                font-size: 20px; 
                font-weight: bold; 
                color: #2196F3; 
            }}
            .amount {{ 
                color: #4CAF50; 
                font-weight: bold; 
                font-size: 16px;
            }}
            .spending {{ 
                color: #f44336; 
                font-weight: bold;
                font-size: 16px;
            }}
            .goal-progress {{
                background-color: #e3f2fd;
                border-left: 4px solid #2196F3;
                padding: 15px;
                margin: 10px 0;
                border-radius: 4px;
            }}
            .category-spending {{
                background-color: #fff3e0;
                border-left: 4px solid #ff9800;
                padding: 10px;
                margin: 5px 0;
                border-radius: 4px;
            }}
            .btn {{
                display: inline-block;
                padding: 12px 24px;
                background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                color: white;
                text-decoration: none;
                border-radius: 25px;
                font-weight: bold;
                margin: 10px 0;
            }}
            .emoji {{ font-size: 24px; }}
            ul {{ padding-left: 20px; }}
            li {{ margin: 8px 0; }}
            h3 {{ color: #2c3e50; margin-top: 0; }}
            h4 {{ color: #34495e; margin-bottom: 10px; }}
            .stats-grid {{
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 15px;
                margin: 20px 0;
            }}
            .stat-card {{
                background: #f8f9fa;
                padding: 15px;
                border-radius: 8px;
                text-align: center;
                border: 1px solid #dee2e6;
            }}
            .stat-value {{
                font-size: 24px;
                font-weight: bold;
                color: #4CAF50;
                display: block;
            }}
            .stat-label {{
                font-size: 12px;
                color: #6c757d;
                text-transform: uppercase;
                margin-top: 5px;
            }}
            @media (max-width: 600px) {{
                .email-container {{ margin: 10px; }}
                .content {{ padding: 20px; }}
                .stats-grid {{ grid-template-columns: 1fr; }}
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h2><span class="emoji">💰</span> {title}</h2>
            </div>
            <div class="content">
                {content}
            </div>
            <div class="footer">
                <p>This is an automated message from Kids Pocket Money Tracker</p>
                <p>Help your children learn valuable financial skills! 🌟</p>
            </div>
        </div>
    </body>
    </html>
    """

def get_daily_reminder_template(child_name: str, current_balance: float) -> str:
    """Template for daily spending reminders"""
    content = f"""
    <h3>Hi {child_name}! <span class="emoji">👋</span></h3>
    <p>Don't forget to record your spending for today!</p>
    
    <div class="highlight">
        <p><strong>Current Balance:</strong> <span class="balance">₹{current_balance:.2f}</span></p>
    </div>
    
    <p>Recording your daily expenses helps you:</p>
    <ul>
        <li><strong>Track your progress</strong> towards your savings goals</li>
        <li><strong>Understand your spending patterns</strong> and habits</li>
        <li><strong>Make better financial decisions</strong> in the future</li>
        <li><strong>Stay accountable</strong> to your money management goals</li>
    </ul>
    
    <div style="text-align: center; margin: 20px 0;">
        <a href="#" class="btn">Record Today's Spending</a>
    </div>
    
    <p>Even small purchases matter! Keep up the great work with managing your money! <span class="emoji">🌟</span></p>
    """
    return get_base_template(content, "Daily Spending Reminder")

def get_weekly_reminder_template(child_name: str, week_stats: dict, goals: list) -> str:
    """Template for weekly spending reminders with statistics"""
    content = f"""
    <h3>Hi {child_name}! <span class="emoji">📊</span></h3>
    <p>Here's your weekly spending summary:</p>
    
    <div class="stats-grid">
        <div class="stat-card">
            <span class="stat-value">{week_stats['entries_count']}</span>
            <div class="stat-label">Entries This Week</div>
        </div>
        <div class="stat-card">
            <span class="stat-value spending">₹{week_stats['total_spent']:.2f}</span>
            <div class="stat-label">Total Spent</div>
        </div>
        <div class="stat-card">
            <span class="stat-value balance">₹{week_stats['current_balance']:.2f}</span>
            <div class="stat-label">Current Balance</div>
        </div>
        <div class="stat-card">
            <span class="stat-value">{week_stats['avg_per_entry']:.2f}</span>
            <div class="stat-label">Avg Per Entry</div>
        </div>
    </div>
    """
    
    # Performance feedback
    if week_stats['entries_count'] < 3:
        content += """
        <div class="highlight">
            <p><span class="emoji">⚠️</span> <strong>Reminder:</strong> Try to record your spending more regularly!</p>
            <p>Consistent tracking helps you stay on top of your financial goals and builds good money habits.</p>
        </div>
        """
    else:
        content += """
        <div class="highlight">
            <p><span class="emoji">🎉</span> <strong>Great job!</strong> You've been consistent with tracking your spending.</p>
            <p>Your dedication to financial responsibility is paying off!</p>
        </div>
        """
    
    # Goals progress
    if goals:
        content += "<h4>Your Savings Goals Progress:</h4>"
        for goal in goals:
            progress_bar_width = min(100, goal['progress'])
            content += f"""
            <div class="goal-progress">
                <strong>{goal['title']}</strong><br>
                <div style="background: #ddd; border-radius: 10px; overflow: hidden; margin: 5px 0;">
                    <div style="background: linear-gradient(90deg, #4CAF50, #45a049); height: 20px; width: {progress_bar_width}%; transition: width 0.3s;"></div>
                </div>
                {goal['progress']:.1f}% complete (₹{goal['remaining']:.2f} remaining)
            </div>
            """
    
    content += """
    <div style="text-align: center; margin: 30px 0;">
        <a href="#" class="btn">View Full Dashboard</a>
    </div>
    <p>Keep up the excellent work managing your money! <span class="emoji">💪</span></p>
    """
    
    return get_base_template(content, "Weekly Financial Summary")

def get_parent_summary_template(parent_name: str, children_data: list, family_stats: dict) -> str:
    """Template for weekly parent summaries"""
    content = f"""
    <h3>Hi {parent_name}! <span class="emoji">📈</span></h3>
    <p>Here's your weekly summary of your children's financial activities:</p>
    
    <div class="highlight">
        <h4><span class="emoji">👨‍👩‍👧‍👦</span> Family Overview</h4>
        <div class="stats-grid">
            <div class="stat-card">
                <span class="stat-value balance">₹{family_stats['total_balance']:.2f}</span>
                <div class="stat-label">Total Family Balance</div>
            </div>
            <div class="stat-card">
                <span class="stat-value spending">₹{family_stats['total_spent']:.2f}</span>
                <div class="stat-label">Total Spent This Week</div>
            </div>
            <div class="stat-card">
                <span class="stat-value">{family_stats['children_count']}</span>
                <div class="stat-label">Children</div>
            </div>
            <div class="stat-card">
                <span class="stat-value amount">₹{family_stats['total_allowances']:.2f}</span>
                <div class="stat-label">Allowances Given</div>
            </div>
        </div>
    </div>
    """
    
    # Individual child summaries
    for child_data in children_data:
        content += f"""
        <div class="highlight">
            <h4><span class="emoji">👤</span> {child_data['name']}</h4>
            <div class="stats-grid">
                <div class="stat-card">
                    <span class="stat-value balance">₹{child_data['balance']:.2f}</span>
                    <div class="stat-label">Current Balance</div>
                </div>
                <div class="stat-card">
                    <span class="stat-value spending">₹{child_data['week_spent']:.2f}</span>
                    <div class="stat-label">Spent This Week</div>
                </div>
            </div>
            <p><strong>Transactions:</strong> {child_data['transaction_count']} this week</p>
            <p><strong>Allowances Received:</strong> <span class="amount">₹{child_data['allowances_received']:.2f}</span></p>
        """
        
        # Spending categories
        if child_data['spending_categories']:
            content += "<p><strong>Spending Categories:</strong></p>"
            for category, amount in child_data['spending_categories'].items():
                content += f"""
                <div class="category-spending">
                    <strong>{category}:</strong> <span class="spending">₹{amount:.2f}</span>
                </div>
                """
        
        # Goal progress
        if child_data['goals']:
            content += "<p><strong>Savings Goals:</strong></p>"
            for goal in child_data['goals']:
                status_emoji = "🎯" if goal['progress'] < 50 else "🔥" if goal['progress'] < 100 else "🏆"
                content += f"<p>{status_emoji} <strong>{goal['title']}:</strong> {goal['progress']:.1f}% complete</p>"
        
        content += "</div>"
    
    content += """
    <div style="text-align: center; margin: 30px 0;">
        <a href="#" class="btn">View Full Parent Dashboard</a>
    </div>
    <p>Keep encouraging your children's financial learning journey! <span class="emoji">🌟</span></p>
    <p><em>Regular monitoring and positive reinforcement help children develop healthy financial habits that last a lifetime.</em></p>
    """
    
    return get_base_template(content, "Weekly Family Financial Summary")

def get_allowance_notification_template(child_name: str, amount: float, frequency: str, parent_name: str, new_balance: float, stored_in: str = None) -> str:
    """Template for allowance received notifications"""
    content = f"""
    <h3>Hi {child_name}! <span class="emoji">💰</span></h3>
    <p>Good news! You've received your {frequency} allowance.</p>
    
    <div class="highlight">
        <div class="stats-grid">
            <div class="stat-card">
                <span class="stat-value amount">₹{amount:.2f}</span>
                <div class="stat-label">Amount Received</div>
            </div>
            <div class="stat-card">
                <span class="stat-value balance">₹{new_balance:.2f}</span>
                <div class="stat-label">New Balance</div>
            </div>
        </div>
        <p style="text-align: center; margin: 10px 0;"><strong>From:</strong> {parent_name}</p>
        {f'<p style="text-align: center;"><strong>Stored in:</strong> {stored_in}</p>' if stored_in else ''}
    </div>
    
    <div style="background: linear-gradient(135deg, #e8f5e8 0%, #f0f8f0 100%); padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h4 style="margin-top: 0;"><span class="emoji">💡</span> Smart Money Tips:</h4>
        <ul>
            <li>Consider setting aside some money for your savings goals</li>
            <li>Think about what purchases are most important to you</li>
            <li>Remember to track your spending to stay on budget</li>
            <li>Ask yourself "Do I need it or want it?" before buying</li>
        </ul>
    </div>
    
    <div style="text-align: center; margin: 30px 0;">
        <a href="#" class="btn">Manage Your Money</a>
    </div>
    
    <p>Keep up the great work with managing your money responsibly! <span class="emoji">🌟</span></p>
    """
    
    return get_base_template(content, f"{frequency.title()} Allowance Received!")

def get_goal_achievement_template(child_name: str, goal_title: str, goal_amount: float) -> str:
    """Template for goal achievement notifications"""
    content = f"""
    <h3>Congratulations {child_name}! <span class="emoji">🎉</span></h3>
    <p>You've successfully reached your savings goal!</p>
    
    <div class="highlight">
        <h4 style="text-align: center; color: #4CAF50; margin: 0;">
            <span class="emoji">🏆</span> Goal Achieved! <span class="emoji">🏆</span>
        </h4>
        <p style="text-align: center; font-size: 20px; margin: 20px 0;">
            <strong>{goal_title}</strong>
        </p>
        <p style="text-align: center; font-size: 24px; margin: 10px 0;">
            <span class="amount">₹{goal_amount:.2f}</span>
        </p>
    </div>
    
    <div style="background: linear-gradient(135deg, #fff8e1 0%, #fff3c4 100%); padding: 20px; border-radius: 8px; margin: 20px 0;">
        <p><span class="emoji">🌟</span> <strong>This is a huge achievement!</strong> You've shown incredible discipline and patience in reaching this goal.</p>
        <p>Your dedication to saving money demonstrates that you're developing excellent financial habits that will serve you well throughout your life.</p>
    </div>
    
    <h4><span class="emoji">🎯</span> What's Next?</h4>
    <ul>
        <li>Celebrate your achievement with something special!</li>
        <li>Consider setting a new, even more ambitious savings goal</li>
        <li>Share your success with family and friends</li>
        <li>Think about what you learned during this savings journey</li>
        <li>Maybe help a friend or sibling with their savings goals</li>
    </ul>
    
    <div style="text-align: center; margin: 30px 0;">
        <a href="#" class="btn">Set New Goal</a>
    </div>
    
    <p>You should be incredibly proud of yourself! <span class="emoji">🌟</span></p>
    """
    
    return get_base_template(content, "🏆 Goal Achieved!")

def get_low_balance_warning_template(child_name: str, current_balance: float, threshold: float = 50.0) -> str:
    """Template for low balance warnings"""
    content = f"""
    <h3>Hi {child_name}! <span class="emoji">⚠️</span></h3>
    <p>Just a friendly reminder about your account balance.</p>
    
    <div class="highlight">
        <p style="text-align: center; font-size: 18px;">
            <strong>Current Balance:</strong> <span class="balance">₹{current_balance:.2f}</span>
        </p>
        <p style="text-align: center; color: #f44336;">
            Your balance is getting low!
        </p>
    </div>
    
    <div style="background: linear-gradient(135deg, #fff3e0 0%, #ffe0b3 100%); padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h4 style="margin-top: 0;"><span class="emoji">💡</span> Money Management Tips:</h4>
        <ul>
            <li><strong>Review your recent spending</strong> - look for patterns</li>
            <li><strong>Prioritize your purchases</strong> - focus on needs vs. wants</li>
            <li><strong>Talk to your parents</strong> about your allowance or earning opportunities</li>
            <li><strong>Consider setting a spending limit</strong> for the rest of the week</li>
            <li><strong>Look for ways to earn extra money</strong> through chores or tasks</li>
        </ul>
    </div>
    
    <p>Remember, managing money is a skill that takes practice. Every financial decision is a learning opportunity! <span class="emoji">📚</span></p>
    
    <div style="text-align: center; margin: 30px 0;">
        <a href="#" class="btn">Review Spending</a>
    </div>
    
    <p>You've got this! <span class="emoji">💪</span></p>
    """
    
    return get_base_template(content, "⚠️ Low Balance Alert")

def get_spending_milestone_template(child_name: str, milestone_type: str, amount: float, timeframe: str) -> str:
    """Template for spending milestone notifications"""
    content = f"""
    <h3>Hi {child_name}! <span class="emoji">📊</span></h3>
    <p>We wanted to share an interesting milestone about your spending habits!</p>
    
    <div class="highlight">
        <h4 style="text-align: center; margin: 0;">
            <span class="emoji">🎯</span> Spending Milestone Reached!
        </h4>
        <p style="text-align: center; font-size: 20px; margin: 15px 0;">
            You've spent <span class="spending">₹{amount:.2f}</span> {timeframe}
        </p>
        <p style="text-align: center; color: #666;">
            {milestone_type}
        </p>
    </div>
    
    <div style="background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%); padding: 20px; border-radius: 8px; margin: 20px 0;">
        <h4 style="margin-top: 0;"><span class="emoji">🤔</span> Time for Reflection:</h4>
        <p>This is a great moment to think about your spending patterns:</p>
        <ul>
            <li>Are you happy with how you've been spending your money?</li>
            <li>Have your purchases brought you joy and value?</li>
            <li>Are you still on track with your savings goals?</li>
            <li>Is there anything you'd do differently?</li>
        </ul>
    </div>
    
    <p>Remember, there's no "perfect" way to spend money - it's all about making choices that align with your values and goals! <span class="emoji">⚖️</span></p>
    
    <div style="text-align: center; margin: 30px 0;">
        <a href="#" class="btn">View Spending Details</a>
    </div>
    
    <p>Keep being mindful about your financial choices! <span class="emoji">🌟</span></p>
    """
    
    return get_base_template(content, "📊 Spending Milestone")

def get_financial_report_template(report_data: dict) -> str:
    """Template for comprehensive financial reports"""
    content = f"""
    <h3>Financial Report for {report_data['child_name']} <span class="emoji">📈</span></h3>
    <p><strong>Report Period:</strong> {report_data['report_period']}</p>
    
    <div class="stats-grid">
        <div class="stat-card">
            <span class="stat-value balance">₹{report_data['current_balance']:.2f}</span>
            <div class="stat-label">Current Balance</div>
        </div>
        <div class="stat-card">
            <span class="stat-value spending">₹{report_data['total_spent']:.2f}</span>
            <div class="stat-label">Total Spent</div>
        </div>
        <div class="stat-card">
            <span class="stat-value amount">₹{report_data['total_received']:.2f}</span>
            <div class="stat-label">Total Received</div>
        </div>
        <div class="stat-card">
            <span class="stat-value" style="color: {'#4CAF50' if report_data['net_change'] >= 0 else '#f44336'}">₹{report_data['net_change']:.2f}</span>
            <div class="stat-label">Net Change</div>
        </div>
    </div>
    """
    
    # Spending by category
    if report_data['spending_by_category']:
        content += """
        <h4><span class="emoji">📊</span> Spending Breakdown</h4>
        """
        for category, amount in report_data['spending_by_category'].items():
            percentage = (amount / report_data['total_spent'] * 100) if report_data['total_spent'] > 0 else 0
            content += f"""
            <div class="category-spending">
                <strong>{category}:</strong> <span class="spending">₹{amount:.2f}</span> ({percentage:.1f}%)
                <div style="background: #ddd; border-radius: 10px; overflow: hidden; margin: 5px 0;">
                    <div style="background: #ff9800; height: 8px; width: {percentage}%;"></div>
                </div>
            </div>
            """
    
    # Goals progress
    if report_data['goals']:
        content += """
        <h4><span class="emoji">🎯</span> Savings Goals</h4>
        """
        for goal in report_data['goals']:
            status_color = "#4CAF50" if goal['status'] == 'completed' else "#2196F3" if goal['status'] == 'active' else "#666"
            content += f"""
            <div class="goal-progress">
                <strong>{goal['title']}</strong> 
                <span style="color: {status_color}; font-size: 12px; text-transform: uppercase;">({goal['status']})</span><br>
                <div style="background: #ddd; border-radius: 10px; overflow: hidden; margin: 5px 0;">
                    <div style="background: linear-gradient(90deg, #4CAF50, #45a049); height: 15px; width: {min(100, goal['progress'])}%;"></div>
                </div>
                Target: ₹{goal['target']:.2f} | Progress: {goal['progress']:.1f}%
            </div>
            """
    
    # Transaction summary
    content += f"""
    <div class="highlight">
        <h4><span class="emoji">📝</span> Transaction Summary</h4>
        <div class="stats-grid">
            <div class="stat-card">
                <span class="stat-value">{report_data['transaction_count']}</span>
                <div class="stat-label">Spending Transactions</div>
            </div>
            <div class="stat-card">
                <span class="stat-value">{report_data['allowance_count']}</span>
                <div class="stat-label">Allowances Received</div>
            </div>
        </div>
        {f'<p><strong>Average per transaction:</strong> ₹{report_data["total_spent"] / report_data["transaction_count"]:.2f}</p>' if report_data['transaction_count'] > 0 else ''}
    </div>
    
    <div style="text-align: center; margin: 30px 0;">
        <a href="#" class="btn">View Full Dashboard</a>
    </div>
    
    <p>Use this information to make informed decisions about your future spending and saving! <span class="emoji">🧠</span></p>
    """
    
    return get_base_template(content, "Financial Report")

# Utility functions for template generation
def format_currency(amount: float) -> str:
    """Format currency consistently across templates"""
    return f"₹{amount:.2f}"

def get_emoji_for_amount(amount: float, threshold_low: float = 50, threshold_high: float = 500) -> str:
    """Get appropriate emoji based on amount"""
    if amount < threshold_low:
        return "💸"  # Money with wings (low amount)
    elif amount > threshold_high:
        return "💰"  # Money bag (high amount)
    else:
        return "💵"  # Dollar banknote (medium amount)