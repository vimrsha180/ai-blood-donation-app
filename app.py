from flask import Flask, render_template, request
import csv
import os
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

DONOR_FILE = "donors.csv"

SENDER_EMAIL = "bloodbankofficialfinder@gmail.com"        
SENDER_PASSWORD = "zijcdehhnkknlxzl" 

# Create database
def init_db():
    conn = sqlite3.connect("donors.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS donors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            email TEXT,
            phone TEXT,
            blood_group TEXT,
            city TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()
# ---------------- HOME ----------------
@app.route("/")
def index():
    return render_template("index.html")


# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        phone = request.form.get("phone")
        blood_group = request.form.get("blood_group")
        city = request.form.get("city")

        if not all([name, email, phone, blood_group, city]):
            return "All fields are required"

        # Create file if not exists
        if not os.path.exists(DONOR_FILE):
            with open(DONOR_FILE, "w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["name", "email", "phone", "blood_group", "city"])

        # Duplicate check
        with open(DONOR_FILE, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row["email"] == email or row["phone"] == phone:
                    return "You already registered"

        with open(DONOR_FILE, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                name.strip(),
                email.strip(),
                phone.strip(),
                blood_group.strip(),
                city.strip()
            ])

        return "Registration successful"

    return render_template("register.html")


# ---------------- REQUEST BLOOD ----------------
@app.route("/request", methods=["GET", "POST"])
def request_blood():
    donors = []

    if request.method == "POST":

        blood = request.form.get("blood_group")
        city = request.form.get("city")

        if not blood or not city:
            return "Please select blood group and city"

        blood = blood.strip().lower()
        city = city.strip().lower()

        if not os.path.exists(DONOR_FILE):
            return "No donors registered yet"

        try:
            with open(DONOR_FILE, "r") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    donor_blood = row.get("blood_group", "").strip().lower()
                    donor_city = row.get("city", "").strip().lower()

                    if donor_blood == blood and donor_city == city:
                        donors.append(row)

                        # Safe email send
                        try:
                            send_email(row["email"], blood, city)
                        except Exception as e:
                            print("Email error:", e)

            if not donors:
                return "No matching donors found"

            return render_template("matched.html", donors=donors)

        except Exception as e:
            return f"Server Error: {str(e)}"

    return render_template("request.html")


# ---------------- EMAIL ----------------
def send_email(to_email, blood, city):
    body = f"""
Hello,

Urgent Blood Donation Request

Blood Group: {blood}
City: {city}

Please help if available.

Thank you,
Blood Donation App
"""

    msg = MIMEText(body)
    msg["Subject"] = "Urgent Blood Donation Request"
    msg["From"] = SENDER_EMAIL
    msg["To"] = to_email

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)


# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
