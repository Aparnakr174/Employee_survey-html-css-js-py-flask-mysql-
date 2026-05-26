from flask import Flask, render_template, request, redirect
import mysql.connector
from datetime import datetime

app = Flask(__name__)

# ---------------- DATABASE CONNECTION ----------------
def get_db():

    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="survey_db"
    )


# ---------------- HOME PAGE ----------------
@app.route('/')
def home():

    message = request.args.get("message", "")

    return render_template(
        'index.html',
        message=message
    )


# ---------------- SURVEY PAGE ----------------
@app.route('/survey', methods=['POST'])
def survey():

    db = get_db()
    cursor = db.cursor()

    username = request.form['username']
    email = request.form['email']

    # CHECK IF EMAIL EXISTS
    cursor.execute(
        "SELECT id FROM results WHERE email=%s",
        (email,)
    )

    existing_user = cursor.fetchone()

    cursor.close()
    db.close()

    # IF EMAIL EXISTS
    if existing_user:

        return render_template(
            'index.html',
            message="❌ This email has already submitted the survey."
        )

    # OPEN SURVEY PAGE
    return render_template(
        'survey.html',
        username=username,
        email=email
    )


# ---------------- SUBMIT SURVEY ----------------
@app.route('/submit', methods=['POST'])
def submit():

    db = get_db()
    cursor = db.cursor()

    try:

        username = request.form['username']
        email = request.form['email']

        q1 = int(request.form.get('q1') or 0)
        q2 = int(request.form.get('q2') or 0)
        q3 = int(request.form.get('q3') or 0)
        q4 = int(request.form.get('q4') or 0)
        q5 = int(request.form.get('q5') or 0)

        score = q1 + q2 + q3 + q4 + q5

        submitted_at = datetime.now()

        # CHECK AGAIN BEFORE INSERT
        cursor.execute(
            "SELECT id FROM results WHERE email=%s",
            (email,)
        )

        existing_user = cursor.fetchone()

        if existing_user:

            cursor.close()
            db.close()

            return render_template(
                'index.html',
                message="❌ This email has already submitted the survey."
            )

        sql = """

        INSERT INTO results
        (
            username,
            email,
            score,
            q1,
            q2,
            q3,
            q4,
            q5,
            submitted_at
        )

        VALUES
        (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s
        )

        """

        values = (
            username,
            email,
            score,
            q1,
            q2,
            q3,
            q4,
            q5,
            submitted_at
        )

        cursor.execute(sql, values)

        db.commit()

        return render_template(
            'result.html',
            username=username,
            score=score
        )

    except mysql.connector.Error as err:

        return f"Database Error: {err}"

    finally:

        cursor.close()
        db.close()


# ---------------- ADMIN LOGIN ----------------
@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():

    message = ""

    if request.method == 'POST':

        username = request.form['username']
        password = request.form['password']

        # CHECK LOGIN
        if username == "admin" and password == "1234":

            return redirect('/admin')

        else:

            message = "❌ Invalid username or password"

    return render_template(
        'admin_login.html',
        message=message
    )


# ---------------- ADMIN DASHBOARD ----------------
@app.route('/admin')
def admin():

    db = get_db()
    cursor = db.cursor()

    # GET FILTER VALUES
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    sql = """

    SELECT
        id,
        username,
        email,
        score,
        q1,
        q2,
        q3,
        q4,
        q5,
        submitted_at

    FROM results

    """

    conditions = []
    values = []

    # START DATE FILTER
    if start_date:

        conditions.append("DATE(submitted_at) >= %s")
        values.append(start_date)

    # END DATE FILTER
    if end_date:

        conditions.append("DATE(submitted_at) <= %s")
        values.append(end_date)

    # ADD CONDITIONS
    if conditions:

        sql += " WHERE " + " AND ".join(conditions)

    # ORDER
    sql += " ORDER BY submitted_at DESC"

    cursor.execute(sql, values)

    data = cursor.fetchall()

    cursor.close()
    db.close()

    return render_template(
        'admin.html',
        data=data
    )


# ---------------- DELETE ENTRY ----------------
@app.route('/delete/<int:id>')
def delete_user(id):

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "DELETE FROM results WHERE id=%s",
        (id,)
    )

    db.commit()

    cursor.close()
    db.close()

    return redirect('/admin')


# ---------------- GRAPH DASHBOARD ----------------
@app.route('/graph')
def graph():

    db = get_db()
    cursor = db.cursor()

    cursor.execute(
        "SELECT q1, q2, q3, q4, q5 FROM results"
    )

    rows = cursor.fetchall()

    def count_labels(index):

        counts = {

            "extremely_satisfied": 0,
            "somewhat_satisfied": 0,
            "neutral": 0,
            "somewhat_dissatisfied": 0,
            "extremely_dissatisfied": 0

        }

        for row in rows:

            try:

                value = int(row[index] or 0)

            except:

                value = 0

            if value == 5:

                counts["extremely_satisfied"] += 1

            elif value == 4:

                counts["somewhat_satisfied"] += 1

            elif value == 3:

                counts["neutral"] += 1

            elif value == 2:

                counts["somewhat_dissatisfied"] += 1

            elif value == 1:

                counts["extremely_dissatisfied"] += 1

        return counts

    q1_data = count_labels(0)
    q2_data = count_labels(1)
    q3_data = count_labels(2)
    q4_data = count_labels(3)
    q5_data = count_labels(4)

    cursor.close()
    db.close()

    return render_template(
        'graph.html',
        q1=q1_data,
        q2=q2_data,
        q3=q3_data,
        q4=q4_data,
        q5=q5_data
    )


# ---------------- RUN APP ----------------
if __name__ == '__main__':

    app.run(debug=True)