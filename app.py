from flask import Flask, render_template, request, jsonify, redirect, url_for, session
from enhanced_model import EnhancedReviewDetector
from amazon_scraper import AmazonReviewScraper
from flipkart_scraper import scrape_reviews as flipkart_scrape_reviews
import secrets
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__, template_folder='templates')
app.secret_key = secrets.token_hex(16)

# Initialize the model
detector = EnhancedReviewDetector()

# Sample training data
sample_reviews = [
    "This product is amazing! I love everything about it!",
    "Worst product ever! Don't buy it!!!"
]
sample_labels = [1, 0]  # 1 for genuine, 0 for fake

# Train the model
detector.fit(sample_reviews, sample_labels)

# User storage
USERS_FILE = 'users.json'

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        
        users = load_users()
        
        if username in users:
            return render_template('register.html', error="Username already exists")
        
        if password != confirm_password:
            return render_template('register.html', error="Passwords do not match")
        
        if len(password) < 4:
            return render_template('register.html', error="Password must be at least 4 characters long")
        
        users[username] = generate_password_hash(password)
        save_users(users)
        
        return render_template('register.html', success="Registration successful! You can now login.")
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        users = load_users()
        
        if username not in users:
            return render_template('login.html', error="User not found")
        
        if check_password_hash(users[username], password):
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('scrape'))
        
        return render_template('login.html', error="Invalid password")
    
    return render_template('login.html')

@app.route('/scrape', methods=['GET', 'POST'])
def scrape():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'GET':
        session.pop('reviews', None)
        return render_template('scrape.html')
    
    if request.method == 'POST':
        url = request.form.get('url')
        manual_reviews = request.form.get('manual_reviews')
        action = request.form.get('action')
        
        try:
            reviews = []
            
            # Scrape reviews from URL if provided
            if url and action == 'scrape':
                if 'amazon.in' in url.lower():
                    scraper = AmazonReviewScraper()
                    reviews = scraper.scrape_reviews(url)
                elif 'flipkart.com' in url.lower():
                    reviews = [{'text': review, 'title': 'Flipkart Review'} for review in flipkart_scrape_reviews(url)]
            
            # Use manually pasted reviews if provided
            elif manual_reviews and action == 'analyze':
                reviews = [{'text': review.strip(), 'title': 'Manual Review'} 
                           for review in manual_reviews.split('\n') 
                           if review.strip()]
            
            if not reviews:
                return render_template('scrape.html', error="No reviews found")
            
            session['reviews'] = reviews
            
            # If analyzing manual reviews, go directly to analysis of first review
            if action == 'analyze':
                return redirect(url_for('analyze_review', review_index=0))
            
            return redirect(url_for('reviews'))
        
        except Exception as e:
            return render_template('scrape.html', error=f"Error processing reviews: {str(e)}")
    
    return render_template('scrape.html')

@app.route('/reviews')
def reviews():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    reviews = session.get('reviews', [])
    if not reviews:
        return redirect(url_for('scrape'))
    
    return render_template('reviews.html', reviews=reviews)

@app.route('/analyze/<int:review_index>')
def analyze_review(review_index):
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    reviews = session.get('reviews', [])
    if not reviews or review_index >= len(reviews):
        return redirect(url_for('scrape'))
    
    review = reviews[review_index]
    result = detector.predict(review['text'])
    session['analysis_result'] = result
    
    return redirect(url_for('result'))

@app.route('/result')
def result():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    analysis_result = session.get('analysis_result')
    if not analysis_result:
        return redirect(url_for('scrape'))
    
    return render_template('result.html', result=analysis_result)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.debug = True
    app.run(port=5000)