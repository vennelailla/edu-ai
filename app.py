import os
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "edufuture_ai_secret_2026")

basedir = os.path.abspath(os.path.dirname(__file__))
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + os.path.join(basedir, "edufuture.db")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


# ==================== DATABASE MODELS ====================

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'student', 'teacher', 'parent'
    learning_level = db.Column(db.String(50), default="intermediate")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AssignedAssessment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    weak_topic_focus = db.Column(db.String(100), default="Trigonometry")
    assigned_by = db.Column(db.String(100), nullable=False)
    due_date = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AssessmentSubmission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    assessment_title = db.Column(db.String(150), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    start_time = db.Column(db.String(30), nullable=False)
    submit_time = db.Column(db.String(30), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    warnings_count = db.Column(db.Integer, default=0)
    activity_log_text = db.Column(db.Text, nullable=False)
    final_status = db.Column(db.String(120), nullable=False)
    ai_suggestion = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AttendanceRecord(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(30), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'Present', 'Absent', 'Late'
    remarks = db.Column(db.String(200), default="")
    marked_by = db.Column(db.String(100), nullable=False)


class AIQueryLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_name = db.Column(db.String(100), nullable=False)
    role_context = db.Column(db.String(20), nullable=False)
    prompt = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


def seed_initial_data():
    if AssignedAssessment.query.count() == 0:
        db.session.add_all([
            AssignedAssessment(
                title="Mathematics & Trigonometry Mastery Quiz",
                subject="Mathematics",
                weak_topic_focus="Trigonometry",
                assigned_by="Dr. Aris Thorne",
                due_date="2026-11-20"
            ),
            AssignedAssessment(
                title="Neural Networks & Machine Learning Lab",
                subject="Artificial Intelligence",
                weak_topic_focus="Backpropagation",
                assigned_by="Dr. Aris Thorne",
                due_date="2026-11-24"
            )
        ])
    if AssessmentSubmission.query.count() == 0:
        sample_log = (
            "10:05 AM - Tab Switched [Warning 1]\n"
            "10:12 AM - Copy-Paste Detected\n"
            "10:20 AM - Full Screen Exited [Warning 2]\n"
            "10:25 AM - Asked Edu AI 3 doubts [Allowed]"
        )
        db.session.add(AssessmentSubmission(
            student_name="Alex Johnson",
            assessment_title="Mathematics & Trigonometry Mastery Quiz",
            subject="Mathematics",
            start_time="10:00 AM",
            submit_time="10:30 AM",
            score=85,
            warnings_count=2,
            activity_log_text=sample_log,
            final_status="Completed. 2 Warnings. No auto-submit.",
            ai_suggestion='Student needs help with "Trigonometry". Practice recommended.'
        ))
    if AttendanceRecord.query.count() == 0:
        db.session.add_all([
            AttendanceRecord(
                student_name="Alex Johnson",
                date="2026-11-16",
                status="Present",
                remarks="Active in AI Lab",
                marked_by="Dr. Aris Thorne"
            ),
            AttendanceRecord(
                student_name="Alex Johnson",
                date="2026-11-17",
                status="Present",
                remarks="On time",
                marked_by="Dr. Aris Thorne"
            )
        ])
    db.session.commit()


with app.app_context():
    db.create_all()
    seed_initial_data()


# ==================== ROUTES ====================

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/session", methods=["GET"])
def check_session():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"authenticated": False})
    user = db.session.get(User, user_id)
    if not user:
        session.clear()
        return jsonify({"authenticated": False})
    return jsonify({
        "authenticated": True,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "learning_level": user.learning_level
        }
    })


@app.route("/api/register", methods=["POST"])
def register():
    data = request.get_json()
    name = data.get("name", "").strip()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = data.get("role", "student").lower()
    level = data.get("level", "intermediate").lower()

    if not name or not email or not password:
        return jsonify({"success": False, "message": "All fields are required for sign up."}), 400

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        return jsonify({"success": False, "message": "Email already registered. Please log in instead."}), 400

    new_user = User(
        name=name,
        email=email,
        password_hash=generate_password_hash(password),
        role=role,
        learning_level=level if role == "student" else "N/A"
    )
    db.session.add(new_user)
    db.session.commit()

    session["user_id"] = new_user.id
    session["user_name"] = new_user.name
    session["user_role"] = new_user.role

    return jsonify({
        "success": True,
        "user": {
            "id": new_user.id,
            "name": new_user.name,
            "email": new_user.email,
            "role": new_user.role,
            "learning_level": new_user.learning_level
        }
    })


@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    if not email or not password:
        return jsonify({"success": False, "message": "Email and password are required."}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"success": False, "message": "Invalid email or password."}), 401

    session["user_id"] = user.id
    session["user_name"] = user.name
    session["user_role"] = user.role

    return jsonify({
        "success": True,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "learning_level": user.learning_level
        }
    })


@app.route("/api/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"success": True})


@app.route("/api/dashboard-data", methods=["GET"])
def get_dashboard_data():
    assessments = AssignedAssessment.query.order_by(AssignedAssessment.id.desc()).all()
    submissions = AssessmentSubmission.query.order_by(AssessmentSubmission.id.desc()).all()
    attendance = AttendanceRecord.query.order_by(AttendanceRecord.id.desc()).all()

    return jsonify({
        "assigned_assessments": [
            {
                "id": a.id,
                "title": a.title,
                "subject": a.subject,
                "weak_topic_focus": a.weak_topic_focus,
                "assigned_by": a.assigned_by,
                "due_date": a.due_date
            } for a in assessments
        ],
        "submissions": [
            {
                "id": s.id,
                "student_name": s.student_name,
                "assessment_title": s.assessment_title,
                "subject": s.subject,
                "start_time": s.start_time,
                "submit_time": s.submit_time,
                "score": s.score,
                "warnings_count": s.warnings_count,
                "activity_log_text": s.activity_log_text,
                "final_status": s.final_status,
                "ai_suggestion": s.ai_suggestion
            } for s in submissions
        ],
        "attendance": [
            {
                "id": r.id,
                "student_name": r.student_name,
                "date": r.date,
                "status": r.status,
                "remarks": r.remarks,
                "marked_by": r.marked_by
            } for r in attendance
        ]
    })


@app.route("/api/teacher/assign-assessment", methods=["POST"])
def assign_assessment():
    data = request.get_json()
    title = data.get("title", "").strip()
    subject = data.get("subject", "").strip()
    topic = data.get("topic", "Trigonometry").strip()
    due_date = data.get("due_date", "").strip()
    teacher_name = session.get("user_name", "Dr. Aris Thorne")

    if not title or not subject or not due_date:
        return jsonify({"success": False, "message": "Title, subject, and due date are required."}), 400

    new_assessment = AssignedAssessment(
        title=title,
        subject=subject,
        weak_topic_focus=topic,
        assigned_by=teacher_name,
        due_date=due_date
    )
    db.session.add(new_assessment)
    db.session.commit()
    return jsonify({"success": True, "message": "Assessment assigned successfully."})


@app.route("/api/teacher/attendance", methods=["POST"])
def mark_attendance():
    data = request.get_json()
    student_name = data.get("student_name", "").strip()
    date_val = data.get("date", "").strip()
    status = data.get("status", "Present").strip()
    remarks = data.get("remarks", "").strip()
    teacher_name = session.get("user_name", "Dr. Aris Thorne")

    if not student_name or not date_val:
        return jsonify({"success": False, "message": "Student name and date are required."}), 400

    record = AttendanceRecord(
        student_name=student_name,
        date=date_val,
        status=status,
        remarks=remarks,
        marked_by=teacher_name
    )
    db.session.add(record)
    db.session.commit()
    return jsonify({"success": True, "message": "Attendance saved and synced to Parent Portal."})


@app.route("/api/student/submit-assessment", methods=["POST"])
def submit_assessment():
    data = request.get_json()
    student_name = data.get("student_name") or session.get("user_name", "Alex Johnson")
    assessment_title = data.get("assessment_title", "AI Assessment")
    subject = data.get("subject", "Mathematics")
    weak_topic = data.get("weak_topic", "Trigonometry")
    start_time = data.get("start_time", "10:00 AM")
    submit_time = data.get("submit_time", "10:30 AM")
    score = int(data.get("score", 85))
    warnings_count = int(data.get("warnings_count", 0))
    activity_log_text = data.get("activity_log_text", "No suspicious activity detected.")
    auto_submitted = data.get("auto_submitted", False)

    if auto_submitted:
        final_status = f"Auto-submitted due to 3 Proctoring Warnings."
    else:
        final_status = f"Completed. {warnings_count} Warning{'s' if warnings_count != 1 else ''}. Manual submit."

    if score < 90 or warnings_count > 0:
        ai_suggestion = f'Student needs help with "{weak_topic}". Practice recommended.'
    else:
        ai_suggestion = f'Strong mastery in "{weak_topic}". Ready for advanced modules.'

    submission = AssessmentSubmission(
        student_name=student_name,
        assessment_title=assessment_title,
        subject=subject,
        start_time=start_time,
        submit_time=submit_time,
        score=score,
        warnings_count=warnings_count,
        activity_log_text=activity_log_text,
        final_status=final_status,
        ai_suggestion=ai_suggestion
    )
    db.session.add(submission)
    db.session.commit()

    return jsonify({
        "success": True,
        "submission": {
            "student_name": submission.student_name,
            "start_time": submission.start_time,
            "submit_time": submission.submit_time,
            "score": submission.score,
            "warnings_count": submission.warnings_count,
            "activity_log_text": submission.activity_log_text,
            "final_status": submission.final_status,
            "ai_suggestion": submission.ai_suggestion
        }
    })


@app.route("/api/ai/ask", methods=["POST"])
def ask_ai():
    data = request.get_json()
    prompt = data.get("prompt", "").strip()
    context = data.get("context", "student")
    user_name = session.get("user_name", "Student")

    if not prompt:
        return jsonify({"success": False, "message": "Prompt cannot be empty."}), 400

    if context == "guru_exam":
        reply = (
            f"Edu AI Hint (Exam Safe Mode): Focus on fundamental identities for '{prompt}'. "
            f"Remember: sin²(θ) + cos²(θ) = 1. (Logged as Allowed Doubt)"
        )
    elif context == "chatboard":
        reply = (
            f"EduFuture Chatboard AI: Great question about '{prompt}'! "
            f"Let's break it into 3 clear steps and try a quick practice problem together."
        )
    else:
        reply = (
            f"Edu AI Tutor Explanation for '{prompt}':\n"
            f"1. Concept Overview: Understand the core formula and constraints.\n"
            f"2. Step-by-Step Application: Substitute known values carefully before simplifying."
        )

    log = AIQueryLog(
        user_name=user_name,
        role_context=context,
        prompt=prompt,
        response=reply
    )
    db.session.add(log)
    db.session.commit()

    return jsonify({"success": True, "response": reply})


if __name__ == "__main__":
    app.run(debug=True, port=5000)