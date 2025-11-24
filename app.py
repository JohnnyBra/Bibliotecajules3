import os
import sys
import pandas as pd
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from models import db, User, Book, Loan

if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    static_folder = os.path.join(sys._MEIPASS, 'static')
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
else:
    app = Flask(__name__)

app.config['SECRET_KEY'] = 'bibliohispa_secret_key_123' # In production, use env var
# Fix for DB path in frozen mode (optional, but good if we want the DB near the exe)
if getattr(sys, 'frozen', False):
    # Store DB in the same directory as the executable
    base_dir = os.path.dirname(sys.executable)
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(base_dir, "bibliohispa.db")}'
    app.config['UPLOAD_FOLDER'] = os.path.join(base_dir, 'uploads')
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///bibliohispa.db'
    app.config['UPLOAD_FOLDER'] = 'uploads'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
ALLOWED_EXTENSIONS = {'csv'}

# Ensure upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db.init_app(app)

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    book_of_month = Book.query.filter_by(is_book_of_month=True).first()
    top_readers = User.query.filter_by(role='student').order_by(User.points.desc()).limit(5).all()
    most_read_books = Book.query.order_by(Book.times_borrowed.desc()).limit(5).all()
    return render_template('index.html', book_of_month=book_of_month, top_readers=top_readers, most_read_books=most_read_books)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()

        if user:
            # If admin, check password
            if user.role == 'admin':
                if check_password_hash(user.password, password):
                    login_user(user)
                    return redirect(url_for('admin_dashboard'))
                else:
                    flash('Contraseña incorrecta.')
            else:
                # Logic for students - maybe just class checking or simple password
                # For simplicity, let's assume students also have a password,
                # or we check against their class if we want to be less strict.
                # Prompt says "conste a que clase pertenecen".
                # Let's stick to password for now for consistency, or simple login if password is empty/generic.
                if user.password and check_password_hash(user.password, password):
                     login_user(user)
                     return redirect(url_for('home'))
                else:
                     flash('Login fallido. Verifica tus credenciales.')
        else:
            flash('Usuario no encontrado.')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    # Simple registration for testing, in reality admin might create users or CSV import users too.
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        student_class = request.form.get('student_class')

        if User.query.filter_by(username=username).first():
            flash('El usuario ya existe')
            return redirect(url_for('register'))

        new_user = User(username=username,
                        password=generate_password_hash(password),
                        role='student',
                        student_class=student_class)
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for('home'))
    return render_template('register.html')

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Acceso denegado.')
        return redirect(url_for('home'))

    if request.method == 'POST':
        # Check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            try:
                # Process CSV
                # CSV columns expected: Title, Author, ISBN, Copies
                df = pd.read_csv(filepath)
                for index, row in df.iterrows():
                    isbn = str(row['ISBN'])
                    existing_book = Book.query.filter_by(isbn=isbn).first()
                    if existing_book:
                        # Update copies
                        existing_book.total_copies += int(row['Copies'])
                        existing_book.available_copies += int(row['Copies'])
                    else:
                        new_book = Book(
                            title=row['Title'],
                            author=row['Author'],
                            isbn=isbn,
                            total_copies=int(row['Copies']),
                            available_copies=int(row['Copies'])
                        )
                        db.session.add(new_book)
                db.session.commit()
                flash('Libros importados correctamente.')
            except Exception as e:
                flash(f'Error al procesar CSV: {e}')

    books = Book.query.all()
    active_loans = Loan.query.filter_by(returned=False).all()
    return render_template('admin.html', books=books, active_loans=active_loans)

@app.route('/admin/set_month_book/<int:book_id>')
@login_required
def set_month_book(book_id):
    if current_user.role != 'admin':
        return redirect(url_for('home'))

    # Reset current month book
    Book.query.update({Book.is_book_of_month: False})

    # Set new one
    book = Book.query.get(book_id)
    if book:
        book.is_book_of_month = True
        db.session.commit()
        flash(f'{book.title} es ahora el Libro del Mes.')

    return redirect(url_for('admin_dashboard'))

@app.route('/catalog')
def catalog():
    search = request.args.get('search')
    if search:
        books = Book.query.filter(Book.title.contains(search) | Book.author.contains(search)).all()
    else:
        books = Book.query.all()
    return render_template('catalog.html', books=books)

@app.route('/borrow/<int:book_id>')
@login_required
def borrow_book(book_id):
    book = Book.query.get_or_404(book_id)

    if book.available_copies > 0:
        # Create Loan
        loan = Loan(user_id=current_user.id, book_id=book.id)
        book.available_copies -= 1
        book.times_borrowed += 1
        db.session.add(loan)
        db.session.commit()
        flash(f'Has cogido prestado: {book.title}')
    else:
        flash('No quedan copias disponibles.')

    return redirect(url_for('catalog'))

@app.route('/return/<int:loan_id>')
@login_required
def return_book(loan_id):
    loan = Loan.query.get_or_404(loan_id)

    # Only admin can mark books as returned
    if current_user.role != 'admin':
        flash('Solo los profesores pueden marcar libros como devueltos.')
        return redirect(url_for('profile'))

    if not loan.returned:
        loan.returned = True
        loan.return_date = datetime.utcnow()

        book = Book.query.get(loan.book_id)
        book.available_copies += 1

        # Gamification: Add points
        # Assuming 10 points per book
        user = User.query.get(loan.user_id)
        user.points += 10
        user.books_read_count += 1

        db.session.commit()
        flash(f'Libro devuelto. {user.username} ha ganado 10 puntos!')

    return redirect(url_for('admin_dashboard')) # Redirect to admin dashboard or user profile

@app.route('/profile')
@login_required
def profile():
    loans = Loan.query.filter_by(user_id=current_user.id).order_by(Loan.loan_date.desc()).all()
    return render_template('profile.html', loans=loans)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Create Admin if not exists
        if not User.query.filter_by(role='admin').first():
            admin = User(username='admin', role='admin', password=generate_password_hash('admin123'))
            db.session.add(admin)
            db.session.commit()

    # Disable debug mode if running as frozen executable to prevent infinite reload loops
    is_frozen = getattr(sys, 'frozen', False)
    app.run(debug=not is_frozen, host='0.0.0.0', port=5000)
