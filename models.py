from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=True) # Can be null for kids if we just use class+name, but safer to have
    role = db.Column(db.String(20), nullable=False, default='student') # 'student' or 'admin'
    student_class = db.Column(db.String(20)) # e.g. "5A"
    points = db.Column(db.Integer, default=0)
    books_read_count = db.Column(db.Integer, default=0)

    loans = db.relationship('Loan', backref='user', lazy=True)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100))
    isbn = db.Column(db.String(20), unique=True)
    total_copies = db.Column(db.Integer, default=1)
    available_copies = db.Column(db.Integer, default=1)
    is_book_of_month = db.Column(db.Boolean, default=False)
    times_borrowed = db.Column(db.Integer, default=0) # For "Most Read" stats

    loans = db.relationship('Loan', backref='book', lazy=True)

class Loan(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    loan_date = db.Column(db.DateTime, default=datetime.utcnow)
    return_date = db.Column(db.DateTime, nullable=True)
    returned = db.Column(db.Boolean, default=False)
