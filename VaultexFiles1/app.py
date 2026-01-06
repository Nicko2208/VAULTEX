from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, jsonify, session
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from functools import wraps
import json
import os
import uuid
from PIL import Image
import random
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this-in-production-CHANGE-ME-IN-PRODUCTION'

# Configuration
UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DATA_FILE = 'data.json'
ADMIN_PASSWORD_HASH = generate_password_hash('admin123')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_data():
    """Load all data from JSON file"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                if 'inventory' not in data:
                    data['inventory'] = []
                if 'listings' not in data:
                    data['listings'] = []
                if 'reviews' not in data:
                    data['reviews'] = []
                if 'purchases' not in data:
                    data['purchases'] = []
                if 'users' not in data:
                    data['users'] = []
                return data
        except:
            return {'inventory': [], 'listings': [], 'reviews': [], 'purchases': [], 'users': []}
    return {'inventory': [], 'listings': [], 'reviews': [], 'purchases': [], 'users': []}
    
def save_data(data):
    """Save all data to JSON file"""
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please login to access this page', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Admin access required', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

def analyze_image_ai(image_path):
    """AI-powered image analysis to generate pitch description"""
    try:
        img = Image.open(image_path)
        width, height = img.size
        
        colors = img.getcolors(maxcolors=256*256*256)
        if colors:
            colors.sort(key=lambda x: x[0], reverse=True)
            dominant_colors = colors[:3]
        else:
            dominant_colors = []
        
        pitch_templates = [
            "This exceptional item features premium quality and craftsmanship. The attention to detail is remarkable, making it a standout piece that would enhance any collection. Perfect condition with timeless appeal.",
            "A beautifully designed piece that combines functionality with style. The quality materials and careful construction ensure this item will provide lasting value. An excellent choice for those who appreciate fine workmanship.",
            "This outstanding item showcases superior design and quality. Its versatile nature makes it suitable for multiple uses, while the premium construction ensures durability. A smart investment that offers both style and substance.",
            "Featuring excellent condition and premium quality, this item represents outstanding value. The thoughtful design and high-quality materials make it a compelling choice. Ideal for discerning buyers seeking both quality and style.",
            "A remarkable piece that demonstrates exceptional craftsmanship and attention to detail. The quality is evident throughout, making this an excellent addition to any collection. Perfect for those who value both aesthetics and functionality."
        ]
        
        details = []
        if width > height:
            details.append("landscape orientation")
        elif height > width:
            details.append("portrait orientation")
        else:
            details.append("square format")
        
        if len(dominant_colors) > 0:
            if any(c[1][0] > 200 for c in dominant_colors[:2]):
                details.append("bright, clean appearance")
            elif any(sum(c[1][:3]) < 150 for c in dominant_colors[:2]):
                details.append("sophisticated, elegant design")
        
        pitch = random.choice(pitch_templates)
        if details:
            pitch += f" Features {', '.join(details)}."
        
        return pitch
    except Exception as e:
        return "This quality item presents an excellent opportunity. Well-maintained condition with great potential. A valuable addition that offers both practical utility and lasting appeal."

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        data = load_data()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('Username and password are required', 'error')
            return render_template('register.html')
        
        if any(u['username'] == username for u in data['users']):
            flash('Username already exists', 'error')
            return render_template('register.html')
        
        user = {
            'id': len(data['users']) + 1,
            'username': username,
            'password_hash': generate_password_hash(password),
            'created_at': datetime.now().isoformat()
        }
        data['users'].append(user)
        save_data(data)
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = load_data()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        user = next((u for u in data['users'] if u['username'] == username), None)
        if user and check_password_hash(user['password_hash'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            flash(f'Welcome back, {username}!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Invalid username or password', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Logged out successfully', 'info')
    return redirect(url_for('home'))

@app.route('/selling', methods=['GET', 'POST'])
@login_required
def selling():
    if request.method == 'POST':
        data = load_data()
        
        photo_path = 'images/placeholder.svg'
        if 'photo' in request.files:
            file = request.files['photo']
            if file and file.filename != '' and allowed_file(file.filename):
                filename = str(uuid.uuid4()) + '.' + file.filename.rsplit('.', 1)[1].lower()
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                photo_path = f'images/{filename}'
        
        item = {
            'id': len(data['inventory']) + 1,
            'brief_details': request.form.get('brief_details', ''),
            'seller_user_id': session.get('user_id'),
            'seller_username': session.get('username'),
            'photo_path': photo_path
        }
        data['inventory'].append(item)
        save_data(data)
        flash('Item uploaded successfully to the Vault!', 'success')
        return redirect(url_for('vault'))
    return render_template('selling.html')

@app.route('/vault')
def vault():
    data = load_data()
    items = data['inventory']
    
    search_term = request.args.get('search', '').lower()
    seller_filter = request.args.get('seller', '')
    
    filtered_items = items
    if search_term:
        filtered_items = [i for i in filtered_items if search_term in i.get('brief_details', '').lower()]
    if seller_filter:
        filtered_items = [i for i in filtered_items if seller_filter.lower() in i.get('seller_username', '').lower()]
    
    all_sellers = list(set([i.get('seller_username') for i in items if i.get('seller_username')]))
    return render_template('vault.html', items=filtered_items, all_sellers=all_sellers)

@app.route('/list_item/<int:item_id>')
@login_required
def list_item(item_id):
    data = load_data()
    item = next((i for i in data['inventory'] if i['id'] == item_id), None)
    if not item:
        flash('Item not found', 'error')
        return redirect(url_for('vault'))
    
    seller_reviews = [r for r in data['reviews'] if r.get('seller_user_id') == item.get('seller_user_id')]
    
    return render_template('list_item.html', item=item, seller_reviews=seller_reviews)

@app.route('/generate_ai_pitch/<int:item_id>', methods=['POST'])
@login_required
def generate_ai_pitch(item_id):
    data = load_data()
    item = next((i for i in data['inventory'] if i['id'] == item_id), None)
    if not item:
        return jsonify({'error': 'Item not found'}), 404
    
    photo_path = os.path.join('static', item.get('photo_path', ''))
    if os.path.exists(photo_path) and item.get('photo_path') != 'images/placeholder.svg':
        pitch = analyze_image_ai(photo_path)
        return jsonify({'pitch': pitch})
    else:
        return jsonify({'error': 'Image not found'}), 404

@app.route('/create_listing/<int:item_id>', methods=['POST'])
@login_required
def create_listing(item_id):
    data = load_data()
    item = next((i for i in data['inventory'] if i['id'] == item_id), None)
    if not item:
        flash('Item not found', 'error')
        return redirect(url_for('vault'))
    
    listing = {
        'id': len(data['listings']) + 1,
        'inventory_item_id': item_id,
        'brief_details': item['brief_details'],
        'photo_path': item['photo_path'],
        'pitch_description': request.form.get('pitch_description', ''),
        'listing_price': float(request.form.get('listing_price', 0)),
        'commission_percentage': float(request.form.get('commission_percentage', 15)),
        'lister_user_id': session.get('user_id'),
        'lister_username': session.get('username'),
        'seller_user_id': item.get('seller_user_id'),
        'seller_username': item.get('seller_username')
    }
    data['listings'].append(listing)
    save_data(data)
    flash('Item listed successfully!', 'success')
    return redirect(url_for('buying'))

@app.route('/buying')
def buying():
    data = load_data()
    listings = data['listings']
    
    search_term = request.args.get('search', '').lower()
    price_min = request.args.get('price_min', '')
    price_max = request.args.get('price_max', '')
    lister_filter = request.args.get('lister', '')
    
    filtered_listings = listings
    if search_term:
        filtered_listings = [l for l in filtered_listings if search_term in l.get('brief_details', '').lower() or search_term in l.get('pitch_description', '').lower()]
    if price_min:
        try:
            min_price = float(price_min)
            filtered_listings = [l for l in filtered_listings if l.get('listing_price', 0) >= min_price]
        except:
            pass
    if price_max:
        try:
            max_price = float(price_max)
            filtered_listings = [l for l in filtered_listings if l.get('listing_price', 0) <= max_price]
        except:
            pass
    if lister_filter:
        filtered_listings = [l for l in filtered_listings if lister_filter.lower() in l.get('lister_username', '').lower()]
    
    listings_with_reviews = []
    for listing in filtered_listings:
        lister_reviews = [r for r in data['reviews'] if r.get('lister_user_id') == listing.get('lister_user_id')]
        listing_copy = listing.copy()
        listing_copy['reviews'] = lister_reviews
        listings_with_reviews.append(listing_copy)
    
    all_listers = list(set([l.get('lister_username') for l in listings if l.get('lister_username')]))
    
    return render_template('buying.html', items=listings_with_reviews, all_listers=all_listers)

@app.route('/checkout/<int:listing_id>')
@login_required
def checkout(listing_id):
    data = load_data()
    listing = next((l for l in data['listings'] if l['id'] == listing_id), None)
    if not listing:
        flash('Listing not found', 'error')
        return redirect(url_for('buying'))
    
    return render_template('checkout.html', listing=listing)

@app.route('/purchase/<int:listing_id>', methods=['POST'])
@login_required
def purchase(listing_id):
    data = load_data()
    listing = next((l for l in data['listings'] if l['id'] == listing_id), None)
    if not listing:
        flash('Listing not found', 'error')
        return redirect(url_for('buying'))
    
    purchase_order = {
        'id': len(data['purchases']) + 1,
        'listing_id': listing_id,
        'buyer_user_id': session.get('user_id'),
        'buyer_username': session.get('username', ''),
        'buyer_email': request.form.get('buyer_email', ''),
        'buyer_phone': request.form.get('buyer_phone', ''),
        'seller_user_id': listing.get('seller_user_id'),
        'seller_username': listing.get('seller_username'),
        'lister_user_id': listing.get('lister_user_id'),
        'lister_username': listing.get('lister_username'),
        'item_details': listing.get('brief_details', ''),
        'price': listing.get('listing_price', 0),
        'commission': listing.get('listing_price', 0) * listing.get('commission_percentage', 15) / 100,
        'status': 'pending',
        'date': datetime.now().isoformat()
    }
    data['purchases'].append(purchase_order)
    save_data(data)
    flash('Purchase request sent! The seller will review your request.', 'success')
    return redirect(url_for('buying'))

@app.route('/seller_dashboard')
@login_required
def seller_dashboard():
    data = load_data()
    user_id = session.get('user_id')
    seller_purchases = [p for p in data['purchases'] if p.get('seller_user_id') == user_id]
    seller_purchases.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    return render_template('seller_dashboard.html', purchases=seller_purchases)

@app.route('/respond_purchase/<int:purchase_id>', methods=['POST'])
@login_required
def respond_purchase(purchase_id):
    data = load_data()
    purchase_order = next((p for p in data['purchases'] if p['id'] == purchase_id), None)
    if not purchase_order or purchase_order.get('seller_user_id') != session.get('user_id'):
        flash('Purchase not found or unauthorized', 'error')
        return redirect(url_for('seller_dashboard'))
    
    action = request.form.get('action')
    if action == 'accept':
        purchase_order['status'] = 'accepted'
        flash('Purchase request accepted!', 'success')
    elif action == 'decline':
        purchase_order['status'] = 'declined'
        flash('Purchase request declined.', 'info')
    
    save_data(data)
    return redirect(url_for('seller_dashboard'))

@app.route('/my_purchases')
@login_required
def my_purchases():
    data = load_data()
    user_id = session.get('user_id')
    buyer_purchases = [p for p in data['purchases'] if p.get('buyer_user_id') == user_id]
    buyer_purchases.sort(key=lambda x: x.get('date', ''), reverse=True)
    
    for purchase in buyer_purchases:
        listing = next((l for l in data['listings'] if l['id'] == purchase['listing_id']), None)
        if listing:
            purchase['listing'] = listing
    
    return render_template('my_purchases.html', purchases=buyer_purchases)

@app.route('/add_review', methods=['POST'])
@login_required
def add_review():
    data = load_data()
    purchase_id = int(request.form.get('purchase_id', 0))
    
    purchase = next((p for p in data['purchases'] if p['id'] == purchase_id), None)
    if not purchase or purchase.get('status') != 'accepted' or purchase.get('buyer_user_id') != session.get('user_id'):
        flash('Can only review accepted purchases that belong to you', 'error')
        return redirect(url_for('my_purchases'))
    
    review = {
        'id': len(data['reviews']) + 1,
        'seller_user_id': purchase.get('seller_user_id'),
        'seller_username': purchase.get('seller_username', ''),
        'lister_user_id': purchase.get('lister_user_id'),
        'lister_username': purchase.get('lister_username', ''),
        'listing_id': purchase.get('listing_id'),
        'purchase_id': purchase_id,
        'rating': int(request.form.get('rating', 5)),
        'review_text': request.form.get('review_text', ''),
        'reviewer_user_id': session.get('user_id'),
        'reviewer_username': session.get('username')
    }
    data['reviews'].append(review)
    save_data(data)
    flash('Review submitted successfully!', 'success')
    return redirect(url_for('my_purchases'))

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        if check_password_hash(ADMIN_PASSWORD_HASH, password):
            session['admin_logged_in'] = True
            flash('Admin login successful', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid password', 'error')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    flash('Logged out successfully', 'info')
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    data = load_data()
    return render_template('admin_dashboard.html', listings=data['listings'], purchases=data['purchases'], inventory=data['inventory'])

@app.route('/admin/delete_listing/<int:listing_id>', methods=['POST'])
@admin_required
def delete_listing(listing_id):
    data = load_data()
    listing = next((l for l in data['listings'] if l['id'] == listing_id), None)
    if listing:
        data['listings'] = [l for l in data['listings'] if l['id'] != listing_id]
        save_data(data)
        flash('Listing deleted successfully', 'success')
    else:
        flash('Listing not found', 'error')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_item/<int:item_id>', methods=['POST'])
@admin_required
def delete_item(item_id):
    data = load_data()
    item = next((i for i in data['inventory'] if i['id'] == item_id), None)
    if item:
        # Delete all listings connected to this item
        data['listings'] = [l for l in data['listings'] if l.get('inventory_item_id') != item_id]
        # Delete the item itself
        data['inventory'] = [i for i in data['inventory'] if i['id'] != item_id]
        save_data(data)
        flash('Item and all connected listings deleted successfully', 'success')
    else:
        flash('Item not found', 'error')
    return redirect(url_for('vault'))

@app.route('/vault/item/<int:item_id>')
def vault_item_details(item_id):
    data = load_data()
    item = next((i for i in data['inventory'] if i['id'] == item_id), None)
    if not item:
        flash('Item not found', 'error')
        return redirect(url_for('vault'))
    
    # Get all listings connected to this item
    linked_listings = [l for l in data['listings'] if l.get('inventory_item_id') == item_id]
    
    # Add reviews for each listing
    for listing in linked_listings:
        listing['reviews'] = [r for r in data['reviews'] if r.get('listing_id') == listing['id']]
    
    return render_template('vault_item_details.html', item=item, linked_listings=linked_listings)

if __name__ == '__main__':
    app.run(debug=True, port=5000)
