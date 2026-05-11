import os
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.utils import secure_filename
from database import close_db, init_db, create_user, get_user_by_email, save_resume, get_resume_by_id, get_recent_resumes
from utils import extract_text_from_resume, score_resume_and_extract_skills, compute_ats_score

BASE_DIR = Path(__file__).resolve().parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
ALLOWED_EXTENSIONS = {"pdf", "docx"}

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["SECRET_KEY"] = os.environ.get("FLASK_SECRET_KEY", "please-change-this-secret")
app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024

with app.app_context():
    init_db()


@app.teardown_appcontext
def close_database_connection(exception=None):
    close_db()


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(view):
    def wrapped_view(**kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(**kwargs)
    wrapped_view.__name__ = view.__name__
    return wrapped_view


@app.route("/")
def home():
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_user_by_email(email)
        if user and user[4] == password:
            session.clear()
            session["user_id"] = user[0]
            session["user_name"] = user[1]
            flash("Welcome back, {}!".format(user[1]), "success")
            return redirect(url_for("dashboard"))
        flash("Invalid email or password. Please try again.", "danger")
    return render_template("login.html", title="Login")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm", "")
        if not name or not email or not password:
            flash("All fields are required.", "danger")
        elif password != confirm:
            flash("Passwords do not match.", "danger")
        elif get_user_by_email(email):
            flash("An account with that email already exists.", "danger")
        else:
            create_user(name, email, password)
            flash("Account created successfully. Please log in.", "success")
            return redirect(url_for("login"))
    return render_template("signup.html", title="Sign Up")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required
def dashboard():
    user_id = session["user_id"]
    resumes = get_recent_resumes(user_id)
    return render_template("dashboard.html", title="Dashboard", resumes=resumes)


@app.route("/upload", methods=["GET", "POST"])
@login_required
def upload():
    if request.method == "POST":
        if "resume" not in request.files:
            flash("Please choose a resume file to upload.", "danger")
            return redirect(request.url)
        file = request.files["resume"]
        if file.filename == "":
            flash("No file selected.", "danger")
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            upload_path = UPLOAD_FOLDER / filename
            file.save(upload_path)
            try:
                text = extract_text_from_resume(upload_path)
                score, skills, advice = score_resume_and_extract_skills(text)
                resume_id = save_resume(
                    user_id=session["user_id"],
                    filename=filename,
                    score=score,
                    skills=skills,
                    advice=advice,
                )
                flash("Resume uploaded and analyzed successfully.", "success")
                return redirect(url_for("resume_detail", resume_id=resume_id))
            except Exception as error:
                flash("Could not parse the resume. Please upload a valid PDF or DOCX file.", "danger")
                app.logger.error("Resume processing error: %s", error)
        else:
            flash("Only PDF and DOCX files are supported.", "danger")
    return render_template("upload.html", title="Upload Resume")


@app.route("/resume/<int:resume_id>")
@login_required
def resume_detail(resume_id):
    resume = get_resume_by_id(resume_id, session["user_id"])
    if not resume:
        flash("Resume not found.", "warning")
        return redirect(url_for("dashboard"))
    skills = resume[4].split(",") if resume[4] else []
    return render_template(
        "result.html",
        title="Resume Result",
        resume={
            "id": resume[0],
            "filename": resume[2],
            "score": resume[3],
            "skills": skills,
            "advice": resume[5],
            "uploaded_at": resume[6],
        },
    )


@app.route("/ats-match", methods=["GET", "POST"])
@login_required
def ats_match():
    result = None
    if request.method == "POST":
        job_description = request.form.get("job_description", "").strip()
        file = request.files.get("resume")
        if not job_description:
            flash("Please paste a job description.", "danger")
        elif not file or file.filename == "":
            flash("Please upload a resume file.", "danger")
        elif not allowed_file(file.filename):
            flash("Only PDF and DOCX files are supported.", "danger")
        else:
            filename = secure_filename(file.filename)
            upload_path = UPLOAD_FOLDER / filename
            file.save(upload_path)
            try:
                resume_text = extract_text_from_resume(upload_path)
                score, matched, missing = compute_ats_score(resume_text, job_description)
                result = {
                    "score": score,
                    "matched": matched,
                    "missing": missing,
                    "filename": filename,
                }
            except Exception as error:
                flash("Could not parse the resume. Please upload a valid PDF or DOCX file.", "danger")
                app.logger.error("ATS match error: %s", error)
    return render_template("ats.html", title="ATS Match", result=result)


if __name__ == "__main__":
    UPLOAD_FOLDER.mkdir(exist_ok=True)
    app.run(debug=True)
