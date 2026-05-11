# Flask AI Resume Analyzer

A beginner-friendly Flask project for analyzing resumes with login/signup, resume upload, PDF/DOCX parsing, resume scoring, and skill extraction.

## Features

- User signup and login
- Resume upload with PDF and DOCX support
- Text extraction from uploaded resumes
- Resume scoring and advice generation
- Skill extraction from resume content
- SQLite database for user accounts and results
- Modern responsive UI with Flask templates

## Setup

1. Create and activate your Python virtual environment.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python app.py
   ```
4. Open the site at http://127.0.0.1:5000

## Project Structure

- `app.py` — main Flask application and routes
- `database.py` — SQLite database helpers
- `utils.py` — resume parsing and scoring logic
- `templates/` — HTML views
- `static/css/` — responsive styling
- `uploads/` — saved resume uploads

## Notes

The app uses a simple scoring model for demonstration. You can extend it with more AI-based resume analysis, natural language processing, and richer score components.
