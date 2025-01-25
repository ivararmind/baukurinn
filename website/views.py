import matplotlib
matplotlib.use('Agg')  
import matplotlib.pyplot as plt
from flask import Blueprint, render_template, request, flash, jsonify, redirect, url_for
from flask_login import login_required, current_user
from .models import Log
from . import db
import json
import io
import base64
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.ticker import FuncFormatter
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta




views  = Blueprint('views', __name__)

@views.route('/', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST':
        item = request.form.get('item')
        category = request.form.get('category')
        importance = request.form.get('importance')
        amount = request.form.get('amount')
        frequency = request.form.get('frequency')  # This will come from the automatic payment form

        # Validate inputs for normal expenses
        if len(item) < 1:
            flash('Það verður að skrifa hlut', category='error')
        elif len(category) < 1:
            flash('Það verður að velja tegund', category='error')
        elif len(importance) < 1:
            flash('Það verður að velja mikilvægi', category='error')
        elif int(amount) <= 0:
            flash('Hluturinn verður að hafa verð stærra en 0', category='error')
        else:

            if frequency:
                current_date = datetime.utcnow()
                next_payment_date = calculate_next_payment_date(frequency, current_date)

                # Create the log for the recurring expense, including its frequency and next payment date
                new_log = Log(
                    item=item,
                    category=category,
                    importance=importance,
                    amount=int(amount),
                    user_id=current_user.id,
                    frequency=frequency,  
                    next_payment_date=next_payment_date,  
                )

                # Also create an immediate normal expense (for the first instance of the recurring expense)
                normal_expense = Log(
                    item=item,
                    category=category,
                    importance=importance,
                    amount=int(amount),
                    user_id=current_user.id
                )
                db.session.add(normal_expense)

            else:
                # For normal expense (non-recurring)
                new_log = Log(
                    item=item,
                    category=category,
                    importance=importance,
                    amount=int(amount),
                    user_id=current_user.id
                )
                db.session.add(new_log)

            db.session.add(new_log)
            db.session.commit()

            flash('Færsla skráð!', category='success')
            return redirect(url_for('views.home'))  # Redirect to GET request

    # Get all logs for the current user
    logs = Log.query.filter_by(user_id=current_user.id).all()

    # Process Recurring Payments: Move them to normal expenses as they come due
    for log in logs:
        if log.frequency and log.next_payment_date <= datetime.utcnow():
            # Add a new normal expense for the recurring payment
            normal_expense = Log(
                item=log.item,
                category=log.category,
                importance=log.importance,
                amount=log.amount,
                user_id=log.user_id
            )
            db.session.add(normal_expense)

            # Update the recurring expense's next payment date
            next_payment_date = calculate_next_payment_date(log.frequency, datetime.utcnow())
            log.next_payment_date = next_payment_date

    db.session.commit()

    # Separate logs for rendering
    normal_logs = [log for log in logs if not log.frequency]  # Non-recurring logs (normal expenses)
    recurring_logs = [log for log in logs if log.frequency]   # Recurring logs (with upcoming payments)

    # Sort normal logs to show the newest ones at the top by 'date' (newest first)
    normal_logs.sort(key=lambda log: log.date, reverse=True)

    # Sort recurring logs to show the next payment at the top (upcoming payments)
    recurring_logs.sort(key=lambda log: log.next_payment_date)

    return render_template("home.html", user=current_user, normal_logs=normal_logs, recurring_logs=recurring_logs)

    

@views.route('/report-automatic', methods=['POST'])
@login_required
def report_automatic():
    data = request.get_json()
    item = data.get('item')
    category = data.get('category')
    importance = data.get('importance')
    amount = data.get('amount')
    frequency = data.get('frequency')

    # Validation
    if not item or not category or not importance or not amount or not frequency:
        return jsonify({"success": False, "error": "All fields are required"}), 400

    try:
        amount = int(amount)
        if amount <= 0:
            raise ValueError("Amount must be greater than 0")
    except ValueError:
        return jsonify({"success": False, "error": "Invalid amount"}), 400

    # Get the current date (assume it's the first payment date)
    current_date = datetime.utcnow()

    # Calculate the next payment date based on the frequency
    next_payment_date = calculate_next_payment_date(frequency, current_date)

    # Create a new log entry for recurring payment
    new_log = Log(
        item=item,
        category=category,
        importance=importance,
        amount=amount,
        user_id=current_user.id,
        frequency=frequency,  # Save frequency for recurring payments
        next_payment_date=next_payment_date,  # Save the next payment date
    )
    db.session.add(new_log)
    db.session.commit()

    return jsonify({"success": True})


def calculate_next_payment_date(frequency, last_payment_date):
    if frequency == 'monthly':
        return last_payment_date + timedelta(days=30)  
    elif frequency == 'weekly':
        return last_payment_date + timedelta(weeks=1)  
    elif frequency == 'yearly':
        return last_payment_date + timedelta(weeks=52)  
    else:
        return last_payment_date 



@views.route('/delete-expense', methods=['POST'])
def delete_expense():
    expense = json.loads(request.data)
    expenseId = expense['expenseId']
    expense = Log.query.get(expenseId)
    if expense:
        if expense.user_id == current_user.id:
            db.session.delete(expense)
            db.session.commit()
            return jsonify({"success": True})
    return jsonify({"success": False}), 400






@views.route('/stadan', methods=['GET'])
@login_required
def stadan():
    category_names = {
        "fun": "Skemmtun",
        "eatout": "Út að borða",
        "health": "Heilsa",
        "groceries": "Matarinnkaup",
        "clothing": "Föt",
        "living": "Heimiliskostnaður",
        "trans": "Samgöngur",
        "misc": "Ýmis annað"
    }

    all_categories = ["fun", "eatout", "health", "groceries", "clothing", "living", "trans", "misc"]

    importance_names = {
        "essential": "Nauðsynlegt",
        "need": "Gott að hafa",
        "nice": "Lúxus",
        "shouldnt": "Ætti ekki"
    }

    all_importances = ["essential", "need", "nice", "shouldnt"]

    month_names = [
        "Janúar", "Febrúar", "Mars", "Apríl", "Maí", "Júní",
        "Júlí", "Ágúst", "September", "Október", "Nóvember", "Desember"
    ]

    time_period = request.args.get('time_period', 'overall')

    logs = Log.query.filter_by(user_id=current_user.id).all()
    now = datetime.utcnow()

    # Filter logs by time period
    if time_period == 'this_month':
        logs = [log for log in logs if log.date and log.date.year == now.year and log.date.month == now.month]
    elif time_period == 'last_month':
        last_month = now - relativedelta(months=1)
        logs = [log for log in logs if log.date and log.date.year == last_month.year and log.date.month == last_month.month]

    # Total spending calculation
    total_spending = sum([log.amount for log in logs])

    # Initialize spending data
    spending_by_category = {category: 0 for category in all_categories}
    spending_by_importance = {importance: 0 for importance in all_importances}

    if total_spending > 0:
        for log in logs:
            spending_by_category[log.category] += log.amount
            if log.importance:
                spending_by_importance[log.importance] += log.amount

    # Convert to Icelandic
    spending_by_category_icelandic = {category_names[cat]: spending_by_category[cat] for cat in all_categories}
    spending_by_importance_icelandic = {importance_names[imp]: spending_by_importance[imp] for imp in all_importances}

    categories = list(spending_by_category_icelandic.keys())
    amounts = list(spending_by_category_icelandic.values())
    importance_categories = list(spending_by_importance_icelandic.keys())
    importance_amounts = list(spending_by_importance_icelandic.values())

    # Generate charts if there are expenses
    chart_img = ""
    importance_chart_img = ""
    monthly_chart_img = ""

    if total_spending > 0:
        # Donut chart for categories
        fig, ax = plt.subplots(figsize=(7, 7))
        nonzero_amounts = [amt for amt in amounts if amt > 0]
        nonzero_categories = [categories[i] for i, amt in enumerate(amounts) if amt > 0]

        if nonzero_amounts:
            ax.pie(nonzero_amounts, labels=nonzero_categories, startangle=90, wedgeprops={'width': 0.4})
            ax.axis('equal')

        img = io.BytesIO()
        FigureCanvas(fig).print_png(img)
        img.seek(0)
        chart_img = base64.b64encode(img.getvalue()).decode('utf8')

        # Bar chart for months
        monthly_totals = [0] * 12
        for log in logs:
            if log.date:
                month_index = log.date.month - 1
                if log.frequency == 'weekly':
                    monthly_totals[month_index] += log.amount * 4.35
                elif log.frequency == 'monthly':
                    monthly_totals[month_index] += log.amount
                else:
                    monthly_totals[month_index] += log.amount

        fig, ax = plt.subplots(figsize=(10, 6))
        ax.bar(month_names, monthly_totals, color="#FF5733")
        ax.tick_params(axis='x', rotation=45)
        ax.grid(axis='y', linestyle='--', alpha=0.7)

        img = io.BytesIO()
        FigureCanvas(fig).print_png(img)
        img.seek(0)
        monthly_chart_img = base64.b64encode(img.getvalue()).decode('utf8')

        # Donut chart for importance
        fig2, ax2 = plt.subplots(figsize=(7, 7))
        nonzero_importance_amounts = [amt for amt in importance_amounts if amt > 0]
        nonzero_importance_categories = [importance_categories[i] for i, amt in enumerate(importance_amounts) if amt > 0]

        if nonzero_importance_amounts:
            ax2.pie(nonzero_importance_amounts, labels=nonzero_importance_categories, startangle=90, wedgeprops={'width': 0.4})
            ax2.axis('equal')

        img2 = io.BytesIO()
        FigureCanvas(fig2).print_png(img2)
        img2.seek(0)
        importance_chart_img = base64.b64encode(img2.getvalue()).decode('utf8')

    # Total recurring payments
    total_recurring_payments = sum(
        log.amount * (4.35 if log.frequency == 'weekly' else 1)
        for log in logs
        if hasattr(log, 'frequency') and log.frequency in ['weekly', 'monthly']
    )

    


    non_essential_categories = ['shouldnt', 'nice', 'need']
    
    # recurring sem er ekki nauðs
    non_essential_total = sum(
        log.amount * (4.35 if log.frequency == 'weekly' else 1)
        for log in logs
        if hasattr(log, 'frequency') and log.frequency in ['weekly', 'monthly']
        and log.importance in non_essential_categories
    )
        

    return render_template(
        "stadan.html",
        user=current_user,
        logs=logs,
        total_spending=total_spending,
        spending_by_category=spending_by_category_icelandic,
        spending_by_importance=spending_by_importance_icelandic,
        categories=categories,
        amounts=amounts,
        chart_img=chart_img,
        monthly_chart_img=monthly_chart_img,
        importance_chart_img=importance_chart_img,
        total_recurring_payments=total_recurring_payments,
        time_period=time_period,
        total_non_essential_recurring_payments=non_essential_total
        
        )
