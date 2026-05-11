import sqlite3
from pathlib import Path
from flask import g

BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "resume_analyzer.db"


def get_db():
    db = getattr(g, "_database", None)
    if db is None:
        db = sqlite3.connect(str(DATABASE_PATH))
        db.row_factory = sqlite3.Row
        g._database = db
    return db


def close_db(e=None):
    db = getattr(g, "_database", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(str(DATABASE_PATH))
    cursor = db.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL,
            password TEXT NOT NULL
        )
        """
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS resumes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            score INTEGER NOT NULL,
            skills TEXT,
            advice TEXT,
            uploaded_at TEXT NOT NULL,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """
    )
    db.commit()
    db.close()


def create_user(name, email, password):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO users (name, email, created_at, password) VALUES (?, ?, datetime('now'), ?)",
        (name, email, password),
    )
    db.commit()
    return cursor.lastrowid


def get_user_by_email(email):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    return cursor.fetchone()


def get_user_by_id(user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    return cursor.fetchone()


def save_resume(user_id, filename, score, skills, advice):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "INSERT INTO resumes (user_id, filename, score, skills, advice, uploaded_at) VALUES (?, ?, ?, ?, ?, datetime('now'))",
        (user_id, filename, score, skills, advice),
    )
    db.commit()
    return cursor.lastrowid


def get_resume_by_id(resume_id, user_id):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT * FROM resumes WHERE id = ? AND user_id = ?",
        (resume_id, user_id),
    )
    return cursor.fetchone()


def get_recent_resumes(user_id, limit=5):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        "SELECT * FROM resumes WHERE user_id = ? ORDER BY uploaded_at DESC LIMIT ?",
        (user_id, limit),
    )
    return cursor.fetchall()
