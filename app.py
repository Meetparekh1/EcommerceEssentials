import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from werkzeug.security import generate_password_hash, check_password_hash

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Create database base class
class Base(DeclarativeBase):
    pass

# Initialize SQLAlchemy
db = SQLAlchemy(model_class=Base)

# Create the Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure SQLite database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL", "sqlite:///ecommerce.db")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with the extension
db.init_app(app)

# Import models after db initialization to avoid circular imports
with app.app_context():
    from models import User, Product, Category, Order, OrderItem, CartItem, Address
    db.create_all()
    
    # Create initial categories and admin user if they don't exist
    from forms import LoginForm, RegisterForm, AddressForm, CheckoutForm, ProductForm
    
    # Create initial data if database is empty
    if not Category.query.first():
        categories = [
            Category(name="Electronics", description="Electronic devices and gadgets"),
            Category(name="Clothing", description="Fashion clothing for men and women"),
            Category(name="Books", description="Books of various genres"),
            Category(name="Home & Kitchen", description="Home and kitchen appliances"),
            Category(name="Sports", description="Sports equipment and accessories"),
            Category(name="Beauty", description="Beauty and personal care products")
        ]
        db.session.add_all(categories)
        db.session.commit()
        
        # Add some products to each category
        electronics = [
            Product(name="Smartphone", description="Latest smartphone with advanced features", 
                   price=12999.00, stock=50, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/mobile-alt.svg", 
                   category_id=1, featured=True),
            Product(name="Laptop", description="High-performance laptop for professional use", 
                   price=49999.00, stock=30, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/laptop.svg", 
                   category_id=1, featured=True),
            Product(name="Smartwatch", description="Fitness tracking smartwatch", 
                   price=2999.00, stock=100, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/clock.svg", 
                   category_id=1),
            Product(name="Headphones", description="Noise cancelling wireless headphones", 
                   price=1999.00, stock=75, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/headphones.svg", 
                   category_id=1),
            Product(name="Bluetooth Speaker", description="Portable bluetooth speaker with great sound", 
                   price=1499.00, stock=60, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/volume-up.svg", 
                   category_id=1),
            Product(name="Power Bank", description="10000mAh fast charging power bank", 
                   price=999.00, stock=120, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/battery-full.svg", 
                   category_id=1)
        ]
        
        clothing = [
            Product(name="Men's T-Shirt", description="Cotton t-shirt for men", 
                   price=499.00, stock=200, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/tshirt.svg", 
                   category_id=2, featured=True),
            Product(name="Women's Dress", description="Elegant dress for women", 
                   price=1299.00, stock=80, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/female.svg", 
                   category_id=2),
            Product(name="Jeans", description="Comfortable denim jeans", 
                   price=999.00, stock=150, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/user.svg", 
                   category_id=2),
            Product(name="Jacket", description="Winter jacket for cold weather", 
                   price=1999.00, stock=70, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/user-tie.svg", 
                   category_id=2),
            Product(name="Formal Shirt", description="Formal shirt for office wear", 
                   price=799.00, stock=100, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/user-tie.svg", 
                   category_id=2),
            Product(name="Sports Shoes", description="Comfortable sports shoes for running", 
                   price=1499.00, stock=90, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/shoe-prints.svg", 
                   category_id=2, featured=True)
        ]
        
        books = [
            Product(name="Fiction Novel", description="Bestselling fiction novel", 
                   price=299.00, stock=200, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/book.svg", 
                   category_id=3),
            Product(name="Self-Help Book", description="Book for personal development", 
                   price=399.00, stock=150, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/book-reader.svg", 
                   category_id=3, featured=True),
            Product(name="Cookbook", description="Collection of delicious recipes", 
                   price=499.00, stock=100, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/utensils.svg", 
                   category_id=3),
            Product(name="Biography", description="Biography of a famous personality", 
                   price=349.00, stock=80, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/user.svg", 
                   category_id=3),
            Product(name="Academic Textbook", description="College textbook for students", 
                   price=899.00, stock=60, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/graduation-cap.svg", 
                   category_id=3),
            Product(name="Children's Book", description="Illustrated book for children", 
                   price=199.00, stock=120, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/child.svg", 
                   category_id=3)
        ]
        
        home_kitchen = [
            Product(name="Blender", description="Multi-purpose kitchen blender", 
                   price=1999.00, stock=50, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/blender.svg", 
                   category_id=4, featured=True),
            Product(name="Coffee Maker", description="Automatic coffee maker for home", 
                   price=2499.00, stock=40, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/coffee.svg", 
                   category_id=4),
            Product(name="Bedsheet Set", description="Cotton bedsheet set with pillowcases", 
                   price=899.00, stock=100, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/bed.svg", 
                   category_id=4),
            Product(name="Dining Table", description="Wooden dining table for 6 people", 
                   price=12999.00, stock=20, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/chair.svg", 
                   category_id=4),
            Product(name="Microwave Oven", description="Digital microwave oven for kitchen", 
                   price=6999.00, stock=30, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/temperature-high.svg", 
                   category_id=4),
            Product(name="Water Purifier", description="RO water purifier for home", 
                   price=8999.00, stock=25, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/tint.svg", 
                   category_id=4)
        ]
        
        sports = [
            Product(name="Cricket Bat", description="Professional cricket bat", 
                   price=1499.00, stock=50, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/table-tennis.svg", 
                   category_id=5),
            Product(name="Football", description="Standard size football", 
                   price=799.00, stock=80, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/futbol.svg", 
                   category_id=5, featured=True),
            Product(name="Yoga Mat", description="Anti-slip yoga mat for fitness", 
                   price=499.00, stock=100, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/spa.svg", 
                   category_id=5),
            Product(name="Dumbbells", description="Set of 5kg dumbbells", 
                   price=999.00, stock=60, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/dumbbell.svg", 
                   category_id=5),
            Product(name="Badminton Racket", description="Professional badminton racket", 
                   price=899.00, stock=70, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/table-tennis.svg", 
                   category_id=5),
            Product(name="Treadmill", description="Motorized treadmill for home gym", 
                   price=24999.00, stock=15, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/running.svg", 
                   category_id=5)
        ]
        
        beauty = [
            Product(name="Face Cream", description="Moisturizing face cream", 
                   price=499.00, stock=120, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/magic.svg", 
                   category_id=6, featured=True),
            Product(name="Perfume", description="Luxury perfume for men and women", 
                   price=1999.00, stock=80, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/spray-can.svg", 
                   category_id=6),
            Product(name="Hair Dryer", description="Professional hair dryer with styling tools", 
                   price=1499.00, stock=50, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/wind.svg", 
                   category_id=6),
            Product(name="Makeup Kit", description="Complete makeup kit with brushes", 
                   price=2499.00, stock=40, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/palette.svg", 
                   category_id=6),
            Product(name="Hair Serum", description="Anti-frizz hair serum for smooth hair", 
                   price=399.00, stock=100, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/tint.svg", 
                   category_id=6),
            Product(name="Beard Grooming Kit", description="Complete beard grooming kit for men", 
                   price=899.00, stock=60, image_url="https://cdn.jsdelivr.net/npm/@fortawesome/fontawesome-free@6.0.0-beta3/svgs/solid/cut.svg", 
                   category_id=6)
        ]
        
        all_products = electronics + clothing + books + home_kitchen + sports + beauty
        db.session.add_all(all_products)
        db.session.commit()
    
    # Create admin user if not exists
    if not User.query.filter_by(email="admin@example.com").first():
        admin = User(
            name="Admin",
            email="admin@example.com",
            password=generate_password_hash("admin123"),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()

# Import routes after models initialization
from routes import *

# Register error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error="404 - Page Not Found"), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('error.html', error="500 - Internal Server Error"), 500
