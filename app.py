from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import qrcode
import os
from datetime import datetime

app = Flask(__name__)

app.secret_key = "secret123"

# -------------------------
# DATABASE
# -------------------------

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)


# -------------------------
# DATABASE TABLE
# -------------------------

class Violation(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    vehicle_number = db.Column(db.String(20), nullable=False)
    violation_type = db.Column(db.String(100))
    location = db.Column(db.String(100))
    date = db.Column(db.String(20))
    fine_amount = db.Column(db.Integer)
    status = db.Column(db.String(10), default="Unpaid")


# -------------------------
# LOGIN REQUIRED FUNCTION
# -------------------------

def login_required():

    if "admin" not in session:
        return False
    return True


# -------------------------
# LOGIN PAGE
# -------------------------

@app.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == "POST":

        username = request.form['username']
        password = request.form['password']

        if username == "BlessyMiracle" and password == "bm2318":

            session['admin'] = True
            return redirect(url_for('dashboard'))

        else:
            flash("Invalid Login")

    return render_template("login.html")


# -------------------------
# DASHBOARD
# -------------------------

@app.route('/dashboard')
def dashboard():

    if not login_required():
        return redirect(url_for('login'))

    total = Violation.query.count()
    paid = Violation.query.filter_by(status="Paid").count()
    unpaid = Violation.query.filter_by(status="Unpaid").count()

    records = Violation.query.all()

    total_fine = sum(r.fine_amount for r in records)

    recent = Violation.query.order_by(Violation.id.desc()).limit(5).all()

    return render_template(
        "dashboard.html",
        total=total,
        paid=paid,
        unpaid=unpaid,
        total_fine=total_fine,
        recent=recent
    )


# -------------------------
# ADD VIOLATION
# -------------------------

@app.route('/', methods=['GET', 'POST'])
def add_violation():

    if not login_required():
        return redirect(url_for('login'))

    if request.method == "POST":

        vehicle = request.form['vehicle']
        violation = request.form['violation']
        location = request.form['location']
        fine = request.form['fine']

        today = datetime.now().strftime("%Y-%m-%d")

        record = Violation(
            vehicle_number=vehicle,
            violation_type=violation,
            location=location,
            date=today,
            fine_amount=fine
        )

        db.session.add(record)
        db.session.commit()

        generate_qr(record.id)

        flash("Violation Added Successfully")

        return redirect(url_for('history'))

    return render_template("add_violation.html")


# -------------------------
# HISTORY
# -------------------------

@app.route('/history')
def history():

    if not login_required():
        return redirect(url_for('login'))

    vehicle = request.args.get("vehicle")

    if vehicle:
        records = Violation.query.filter_by(vehicle_number=vehicle).all()
    else:
        records = Violation.query.order_by(Violation.id.desc()).all()

    return render_template("history.html", records=records)


# -------------------------
# SEARCH VEHICLE
# -------------------------

@app.route('/search')
def search():

    if not login_required():
        return redirect(url_for('login'))

    vehicle = request.args.get("vehicle_number")

    records = Violation.query.filter(
        Violation.vehicle_number.contains(vehicle)
    ).all()

    return render_template("history.html", records=records)


# -------------------------
# PAYMENT PAGE
# -------------------------

@app.route('/pay/<int:id>')
def pay(id):

    if not login_required():
        return redirect(url_for('login'))

    record = Violation.query.get_or_404(id)

    return render_template("payment.html", record=record)


# -------------------------
# CONFIRM PAYMENT
# -------------------------

@app.route('/confirm_payment/<int:id>')
def confirm_payment(id):

    record = Violation.query.get_or_404(id)

    record.status = "Paid"

    db.session.commit()

    flash("Payment Successful")

    return redirect(url_for('history'))


# -------------------------
# PUBLIC STATUS PAGE
# -------------------------

@app.route('/status/<int:id>')
def status(id):

    record = Violation.query.get_or_404(id)

    return render_template("status.html", record=record)


# -------------------------
# QR CODE GENERATOR
# -------------------------

def generate_qr(id):

    url = f"http://127.0.0.1:5000/status/{id}"

    img = qrcode.make(url)

    folder = "static/qr"

    if not os.path.exists(folder):
        os.makedirs(folder)

    path = f"{folder}/{id}.png"

    img.save(path)


# -------------------------
# LOGOUT
# -------------------------

@app.route('/logout')
def logout():

    session.clear()

    return redirect(url_for('login'))


# -------------------------
# RUN APP
# -------------------------

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(debug=True, host="0.0.0.0")