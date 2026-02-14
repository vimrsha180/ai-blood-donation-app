from flask import Flask, render_template, request
import sqlite3
import smtplib
from email.mime.text import MIMEText

app = Flask(__name__)

SENDER_EMAIL = "bloodbankofficialfinder@gmail.com"
SENDER_PASSWORD = "zijcdehhnkknlxzl"


# ---------------- DATABASE ----------------
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

        conn = sqlite3.connect("donors.db")
        cursor = conn.cursor()

        # Check duplicate
        cursor.execute("SELECT * FROM donors WHERE email=? OR phone=?", (email, phone))
        existing = cursor.fetchone()
        if existing:
            conn.close()
            return "You already registered"

        cursor.execute(
            "INSERT INTO donors (name, email, phone, blood_group, city) VALUES (?, ?, ?, ?, ?)",
            (name.strip(), email.strip(), phone.strip(), blood_group.strip(), city.strip())
        )
        conn.commit()
        conn.close()

        return "Registration successful"

    return render_template("register.html")


# ---------------- REQUEST BLOOD ----------------
@app.route("/request", methods=["GET", "POST"])
def request_blood():
    if request.method == "POST":

        blood = request.form.get("blood_group")
        city = request.form.get("city")

        if not blood or not city:
            return "Please select blood group and city"

        conn = sqlite3.connect("donors.db")
        cursor = conn.cursor()

        cursor.execute(
            "SELECT name, email, phone, blood_group, city FROM donors WHERE lower(blood_group)=? AND lower(city)=?",
            (blood.strip().lower(), city.strip().lower())
        )

        donors = cursor.fetchall()
        conn.close()

        if not donors:
            return "No matching donors found"

        # Send email safely
        for donor in donors:
            try:
                send_email(donor[1], blood, city)
            except Exception as e:
                print("Email error:", e)

        return render_template("matched.html", donors=donors)

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
