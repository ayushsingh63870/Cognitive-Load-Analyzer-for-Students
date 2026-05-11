from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from db_config import init_db
import sqlite3


app = Flask(__name__)
app.secret_key = "secret123"
import sqlite3

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        hashed_password = generate_password_hash(password)

        conn = sqlite3.connect("cognitive_load.db")
        cursor = conn.cursor()

        try:
            cursor.execute(
                "INSERT INTO users (name, email, password) VALUES (?, ?, ?)",
                (name, email, hashed_password)
            )
            conn.commit()
            conn.close()

            return redirect("/login")

        except sqlite3.IntegrityError:
            conn.close()
            return "User already exists. Try different email."

        except Exception as e:
            conn.close()
            return f"Error: {e}"   # 🔥 VERY IMPORTANT for debugging

    return render_template("register.html")

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = sqlite3.connect("cognitive_load.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        conn.close()

        if user and check_password_hash(user[3], password):

            # ✅ Store user email
            session["user"] = email

            # ✅ Role-based access
            if email == "admin@gmail.com":
                session["role"] = "admin"
            else:
                session["role"] = "student"

            return redirect("/dashboard")

        else:
            return "Invalid Email or Password"

    return render_template("login.html")
@app.route("/dashboard")
def dashboard():

    if "user" in session:
     return render_template("dashboard.html", user=session["user"])

    return redirect("/login")
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")
import time

import time

@app.route("/quiz", methods=["GET", "POST"])
def quiz():

    conn = sqlite3.connect("cognitive_load.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions")
    questions = cursor.fetchall()
    conn.close()

    if "q_index" not in session:
        session["q_index"] = 0
        session["total_time"] = 0
        session["correct"] = 0
        session["count"] = 0

    if request.method == "POST":

        q_index = int(request.form["q_index"])
        selected = request.form["answer"]

        current_question = questions[q_index]
        correct_answer = current_question[6]

        is_correct = (selected == correct_answer)

        start_time = float(request.form["start_time"])
        end_time = time.time() * 1000
        time_taken = (end_time - start_time) / 1000

        session["total_time"] += time_taken
        session["count"] += 1

        if is_correct:
            session["correct"] += 1

        q_index += 1
        session["q_index"] = q_index

    else:
        q_index = session["q_index"]

    # 🔥 FINISH QUIZ
    if q_index >= len(questions):

        avg_time = session["total_time"] / session["count"]
        accuracy = session["correct"] / session["count"]

        # ✅ IMPROVED COGNITIVE LOAD LOGIC
        if accuracy >= 0.75 and avg_time <= 5:
            final_load = "Low"
            suggestion = "Excellent performance with fast and accurate responses."

        elif accuracy >= 0.5 and avg_time <= 8:
            final_load = "Medium"
            suggestion = "Good performance, but you can improve speed and accuracy."

        else:
            final_load = "High"
            suggestion = "You may be experiencing cognitive overload. Revise concepts and practice more."

        # SAVE REPORT
        email = session.get("user")

        conn = sqlite3.connect("cognitive_load.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO reports (email, avg_time, accuracy, cognitive_load) VALUES (?, ?, ?, ?)",
            (email, avg_time, accuracy, final_load)
        )

        conn.commit()
        conn.close()

        # RESET ONLY QUIZ DATA
        session.pop("q_index", None)
        session.pop("total_time", None)
        session.pop("correct", None)
        session.pop("count", None)

        return render_template(
            "result.html",
            load=final_load,
            suggestion=suggestion,
            avg_time=round(avg_time, 2),
            accuracy=round(accuracy, 2)  # show in %
        )

    # NEXT QUESTION
    question = questions[q_index]

    return render_template("quiz.html", question=question, q_index=q_index)
@app.route("/forgot", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]
        new_password = request.form["password"]

        hashed_password = generate_password_hash(new_password)

        conn = sqlite3.connect("cognitive_load.db")
        cursor = conn.cursor()

        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        user = cursor.fetchone()

        if user:
            cursor.execute(
                "UPDATE users SET password=? WHERE email=?",
                (hashed_password, email)
            )
            conn.commit()
            conn.close()
            return "Password updated successfully. Go to login."

        else:
            conn.close()
            return "Email not found."

    return render_template("forgot.html")
@app.route("/admin", methods=["GET", "POST"])
def admin():

    # 🔒 Only admin can access
    if session.get("role") != "admin":
        return "Access Denied ❌"

    if request.method == "POST":

        question = request.form["question"]
        op1 = request.form["option1"]
        op2 = request.form["option2"]
        op3 = request.form["option3"]
        op4 = request.form["option4"]
        correct = request.form["correct"]
        difficulty = request.form["difficulty"]

        conn = sqlite3.connect("cognitive_load.db")
        cursor = conn.cursor()

        cursor.execute("""
        INSERT INTO questions 
        (question, option1, option2, option3, option4, correct_answer, difficulty)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (question, op1, op2, op3, op4, correct, difficulty))

        conn.commit()
        conn.close()

        return "Question Added Successfully ✅"

    return render_template("admin.html")
@app.route("/reports")
def reports():

    if "user" not in session:
        return redirect("/login")

    email = session.get("user")

    conn = sqlite3.connect("cognitive_load.db")
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM reports WHERE email = ?", (email,))
    data = cursor.fetchall()

    conn.close()

    return render_template("reports.html", data=data)
if __name__ == "__main__":
    init_db()
    app.run(debug=True)