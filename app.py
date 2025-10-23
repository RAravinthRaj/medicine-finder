from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from dotenv import load_dotenv
import os
from openai import OpenAI
import bcrypt
from datetime import datetime

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///medicines.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# OpenRouter API
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found in .env file. Please add it.")

client = OpenAI(api_key=OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")

# Database Models
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    chats = db.relationship('Chat', backref='user', lazy=True)
    orders = db.relationship('Order', backref='user', lazy=True)

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    total = db.Column(db.Float, nullable=False)
    items = db.relationship('OrderItem', backref='order', lazy=True)

class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    medicine_id = db.Column(db.Integer, db.ForeignKey('medicine.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    price = db.Column(db.Float, nullable=False)
    medicine = db.relationship('Medicine', backref='order_items')

class Chat(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Chat Function
def get_ai_response(user_input, conversation_history=None):
    messages = [
        {
            "role": "system",
            "content": """You are a helpful assistant for a Medicine Availability Finder app.
            Respond concisely and helpfully. If the user asks about medicine availability, price, or stock,
            suggest they use the search bar but offer insights based on common knowledge.
            For general health queries, advise consulting a doctor. Keep responses under 150 words."""
        }
    ]
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": user_input})

    model_priority = [
        "meta-llama/llama-3.1-8b-instruct",
        "google/gemma-7b-it",
        "nousresearch/hermes-2-pro-mistral"
    ]

    for model in model_priority:
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=200,
                temperature=0.7
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"[WARN] Model {model} failed: {e}")
            continue
    return "Sorry, I encountered an issue with all available AI models. Please try again later."

# Create DB and populate with medicines
with app.app_context():
    db.create_all()
    if not Medicine.query.first():
        medicines = [
            Medicine(name="Paracetamol", quantity=100, price=5.99),
            Medicine(name="Ibuprofen", quantity=50, price=7.49),
            Medicine(name="Amoxicillin", quantity=20, price=12.99),
            Medicine(name="Cetirizine", quantity=30, price=6.49),
            Medicine(name="Vitamin C", quantity=80, price=4.99),
            Medicine(name="Omeprazole", quantity=25, price=15.99),
            Medicine(name="Azithromycin", quantity=15, price=18.99),
            Medicine(name="Metformin", quantity=40, price=9.99),
            Medicine(name="Aspirin", quantity=60, price=3.99),
            Medicine(name="Loratadine", quantity=35, price=8.49),
            Medicine(name="Lisinopril", quantity=30, price=11.99),
            Medicine(name="Atorvastatin", quantity=25, price=14.99),
            Medicine(name="Metoprolol", quantity=40, price=10.49),
            Medicine(name="Levothyroxine", quantity=50, price=9.49),
            Medicine(name="Ciprofloxacin", quantity=20, price=13.99),
            Medicine(name="Pantoprazole", quantity=30, price=16.49),
            Medicine(name="Doxycycline", quantity=15, price=17.99),
            Medicine(name="Hydrochlorothiazide", quantity=45, price=8.99),
            Medicine(name="Vitamin D", quantity=70, price=5.49),
            Medicine(name="Folic Acid", quantity=60, price=4.49)
        ]
        db.session.bulk_save_objects(medicines)
        db.session.commit()
    if not User.query.filter_by(email='admin@example.com').first():
        hashed_password = bcrypt.hashpw('admin123'.encode('utf-8'), bcrypt.gensalt())
        admin = User(email='admin@example.com', password=hashed_password, is_admin=True)
        db.session.add(admin)
        db.session.commit()

# Routes
@app.route('/')
def index():
    return render_template('index.html', user=current_user)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if User.query.filter_by(email=email).first():
            flash('Email already registered.', 'error')
            return redirect(url_for('signup'))
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user = User(email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Signup successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.checkpw(password.encode('utf-8'), user.password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('index'))
        flash('Invalid email or password.', 'error')
        return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

@app.route('/profile')
@login_required
def profile():
    orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.date.desc()).all()
    return render_template('profile.html', orders=orders)

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if not current_user.is_admin:
        flash('Access denied. Admins only.', 'error')
        return redirect(url_for('index'))
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            name = request.form.get('name')
            quantity = int(request.form.get('quantity'))
            price = float(request.form.get('price'))
            medicine = Medicine(name=name, quantity=quantity, price=price)
            db.session.add(medicine)
        elif action == 'edit':
            id = int(request.form.get('id'))
            medicine = Medicine.query.get(id)
            if medicine:
                medicine.name = request.form.get('name')
                medicine.quantity = int(request.form.get('quantity'))
                medicine.price = float(request.form.get('price'))
        elif action == 'delete':
            id = int(request.form.get('id'))
            medicine = Medicine.query.get(id)
            if medicine:
                db.session.delete(medicine)
        db.session.commit()
        flash('Medicine updated successfully.', 'success')
        return redirect(url_for('admin'))
    medicines = Medicine.query.all()
    return render_template('admin.html', medicines=medicines)

@app.route('/search', methods=['GET', 'POST'])
def search_medicine():
    if request.method == 'POST':
        medicine_name = request.form.get('medicine_name', '').strip()
        min_price = request.form.get('min_price', type=float)
        max_price = request.form.get('max_price', type=float)
        min_stock = request.form.get('min_stock', type=int)
        page = request.form.get('page', 1, type=int)
        per_page = 6

        query = Medicine.query.filter(Medicine.name.ilike(f'%{medicine_name}%'))
        if min_price:
            query = query.filter(Medicine.price >= min_price)
        if max_price:
            query = query.filter(Medicine.price <= max_price)
        if min_stock:
            query = query.filter(Medicine.quantity >= min_stock)

        medicines = query.paginate(page=page, per_page=per_page, error_out=False)
        results = [{'id': m.id, 'name': m.name, 'quantity': m.quantity, 'price': m.price} for m in medicines.items]
        return jsonify({
            'results': results,
            'has_next': medicines.has_next,
            'has_prev': medicines.has_prev,
            'page': medicines.page,
            'total_pages': medicines.pages
        })
    return render_template('search.html')

@app.route('/chatbot', methods=['GET', 'POST'])
@login_required
def chatbot():
    if request.method == 'POST':
        user_input = request.json.get('message')
        conversation_history = request.json.get('history', [])
        response = get_ai_response(user_input, conversation_history)
        chat = Chat(user_id=current_user.id, message=user_input, response=response)
        db.session.add(chat)
        db.session.commit()
        updated_history = conversation_history + [
            {"role": "user", "content": user_input},
            {"role": "assistant", "content": response}
        ]
        return jsonify({'response': response, 'history': updated_history})
    chats = Chat.query.filter_by(user_id=current_user.id).order_by(Chat.timestamp.asc()).all()
    return render_template('chatbot.html', chats=chats)

@app.route('/cart', methods=['GET'])
@login_required
def cart():
    return render_template('cart.html')

@app.route('/checkout', methods=['POST'])
@login_required
def checkout():
    cart = request.json.get('cart', [])
    if not cart:
        return jsonify({'error': 'Cart is empty'}), 400
    
    total = 0
    order = Order(user_id=current_user.id, total=0)
    db.session.add(order)

    for item in cart:
        if 'id' not in item or not item['id']:
            db.session.rollback()
            return jsonify({'error': f'Missing ID for item {item.get("name", "unknown")}'}), 400
        try:
            total += item['price'] * item['quantity']
        except (KeyError, TypeError):
            db.session.rollback()
            return jsonify({'error': f'Invalid price or quantity for item {item.get("name", "unknown")}'}), 400

        medicine = Medicine.query.get(item['id'])
        if not medicine:
            db.session.rollback()
            return jsonify({'error': f'Medicine {item.get("name", "unknown")} not found in database'}), 400
        if medicine.quantity < item['quantity']:
            db.session.rollback()
            return jsonify({'error': f'Insufficient stock for {item["name"]}'}), 400
        medicine.quantity -= item['quantity']
        order_item = OrderItem(order=order, medicine_id=medicine.id, quantity=item['quantity'], price=item['price'])
        db.session.add(order_item)

    order.total = total
    try:
        db.session.commit()
        return jsonify({'message': f'Checkout successful! Total amount: ₹{total:.2f}'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Checkout failed: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True)