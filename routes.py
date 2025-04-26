from flask import render_template, request, redirect, url_for, flash, session, jsonify, abort
from werkzeug.security import generate_password_hash, check_password_hash
from app import app, db
from models import User, Product, Category, Order, OrderItem, CartItem, Address
from forms import LoginForm, RegisterForm, AddressForm, CheckoutForm, ProductForm
from datetime import datetime
import random
import string
from functools import wraps
from utils.pincodes import is_valid_pincode

# Custom decorators
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'danger')
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please login to access this page', 'danger')
            return redirect(url_for('login', next=request.url))
        
        user = User.query.get(session['user_id'])
        if not user or not user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

# Helper functions
def get_cart_items():
    if 'user_id' in session:
        cart_items = CartItem.query.filter_by(user_id=session['user_id']).all()
        total = sum(item.product.price * item.quantity for item in cart_items)
        return cart_items, total
    return [], 0

def generate_order_number():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

# Route handlers
@app.route('/')
def index():
    featured_products = Product.query.filter_by(featured=True).limit(8).all()
    categories = Category.query.all()
    return render_template('index.html', 
                           featured_products=featured_products, 
                           categories=categories)

@app.route('/category/<int:id>')
def category(id):
    category = Category.query.get_or_404(id)
    page = request.args.get('page', 1, type=int)
    per_page = 6  # Products per page
    
    # Get filter parameters
    min_price = request.args.get('min_price', type=float, default=0)
    max_price = request.args.get('max_price', type=float, default=100000)
    sort_by = request.args.get('sort', 'price_asc')
    
    # Build query
    query = Product.query.filter_by(category_id=id).filter(
        Product.price >= min_price,
        Product.price <= max_price
    )
    
    # Apply sorting
    if sort_by == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort_by == 'newest':
        query = query.order_by(Product.created_at.desc())
    
    # Execute query with pagination
    products = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('category.html', 
                          category=category, 
                          products=products,
                          min_price=min_price,
                          max_price=max_price,
                          sort_by=sort_by)

@app.route('/product/<int:id>')
def product(id):
    product = Product.query.get_or_404(id)
    related_products = Product.query.filter_by(category_id=product.category_id).filter(Product.id != id).limit(4).all()
    return render_template('product.html', product=product, related_products=related_products)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user and check_password_hash(user.password, form.password.data):
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['is_admin'] = user.is_admin
            
            next_page = request.args.get('next')
            flash('Login successful!', 'success')
            
            if next_page:
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('Login unsuccessful. Please check email and password', 'danger')
    
    return render_template('login.html', form=form)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('index'))
    
    form = RegisterForm()
    if form.validate_on_submit():
        # Check if email already exists
        existing_user = User.query.filter_by(email=form.email.data).first()
        if existing_user:
            flash('An account with that email already exists', 'danger')
            return render_template('register.html', form=form)
        
        # Create new user
        hashed_password = generate_password_hash(form.password.data)
        user = User(
            name=form.name.data,
            email=form.email.data,
            password=hashed_password
        )
        
        db.session.add(user)
        db.session.commit()
        
        flash('Account created successfully! You can now login.', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html', form=form)

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_name', None)
    session.pop('is_admin', None)
    flash('You have been logged out', 'success')
    return redirect(url_for('index'))

@app.route('/cart')
def cart():
    cart_items, total = get_cart_items()
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    quantity = int(request.form.get('quantity', 1))
    
    if quantity <= 0:
        flash('Quantity must be positive', 'danger')
        return redirect(url_for('product', id=product_id))
    
    if quantity > product.stock:
        flash(f'Sorry, only {product.stock} items available in stock', 'danger')
        return redirect(url_for('product', id=product_id))
    
    # Check if product already in cart
    cart_item = CartItem.query.filter_by(
        user_id=session['user_id'],
        product_id=product_id
    ).first()
    
    if cart_item:
        # Update quantity if already in cart
        new_quantity = cart_item.quantity + quantity
        if new_quantity > product.stock:
            flash(f'Sorry, only {product.stock} items available in stock', 'danger')
            return redirect(url_for('product', id=product_id))
        
        cart_item.quantity = new_quantity
    else:
        # Add new item to cart
        cart_item = CartItem(
            user_id=session['user_id'],
            product_id=product_id,
            quantity=quantity
        )
        db.session.add(cart_item)
    
    db.session.commit()
    flash('Item added to cart successfully!', 'success')
    
    # Redirect based on action
    if 'buy_now' in request.form:
        return redirect(url_for('checkout'))
    return redirect(url_for('cart'))

@app.route('/cart/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    
    # Ensure user owns this cart item
    if cart_item.user_id != session['user_id']:
        abort(403)
    
    quantity = int(request.form.get('quantity', 1))
    
    if quantity <= 0:
        # Remove item if quantity is 0 or negative
        db.session.delete(cart_item)
        flash('Item removed from cart', 'info')
    else:
        # Update quantity
        if quantity > cart_item.product.stock:
            flash(f'Sorry, only {cart_item.product.stock} items available in stock', 'danger')
            quantity = cart_item.product.stock
        
        cart_item.quantity = quantity
        flash('Cart updated successfully', 'success')
    
    db.session.commit()
    return redirect(url_for('cart'))

@app.route('/cart/remove/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    cart_item = CartItem.query.get_or_404(item_id)
    
    # Ensure user owns this cart item
    if cart_item.user_id != session['user_id']:
        abort(403)
    
    db.session.delete(cart_item)
    db.session.commit()
    
    flash('Item removed from cart', 'success')
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items, total = get_cart_items()
    
    if not cart_items:
        flash('Your cart is empty', 'info')
        return redirect(url_for('cart'))
    
    # Get user addresses
    addresses = Address.query.filter_by(user_id=session['user_id']).all()
    
    # Initialize form and set choices for addresses
    form = CheckoutForm()
    form.address_id.choices = [(a.id, f"{a.address_line1}, {a.city}, {a.state} - {a.pincode}") for a in addresses]
    
    if form.validate_on_submit():
        # Create order
        order = Order(
            user_id=session['user_id'],
            order_number=generate_order_number(),
            total_amount=total,
            address_id=form.address_id.data,
            payment_method=form.payment_method.data
        )
        db.session.add(order)
        db.session.flush()  # Get order ID without committing
        
        # Create order items
        for cart_item in cart_items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=cart_item.product_id,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
            db.session.add(order_item)
            
            # Update product stock
            product = cart_item.product
            product.stock -= cart_item.quantity
            
            # Remove from cart
            db.session.delete(cart_item)
        
        db.session.commit()
        
        # Redirect to payment page with order ID
        return redirect(url_for('payment', order_id=order.id))
    
    # If no address exists, redirect to add address page
    if not addresses:
        flash('Please add a delivery address first', 'info')
        return redirect(url_for('add_address', next=url_for('checkout')))
    
    return render_template('checkout.html', 
                          cart_items=cart_items, 
                          total=total,
                          form=form,
                          addresses=addresses)

@app.route('/payment/<int:order_id>')
@login_required
def payment(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Ensure user owns this order
    if order.user_id != session['user_id']:
        abort(403)
    
    return render_template('payment.html', order=order)

@app.route('/payment/process/<int:order_id>', methods=['POST'])
@login_required
def process_payment(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Ensure user owns this order
    if order.user_id != session['user_id']:
        abort(403)
    
    # Update order status based on payment method
    if order.payment_method == 'cod':
        order.status = 'Processing'
        msg = 'Your order has been placed successfully. Payment will be collected on delivery.'
    else:
        # In a real application, we would integrate with payment gateways here
        order.status = 'Processing'
        msg = 'Payment successful! Your order has been placed.'
    
    db.session.commit()
    flash(msg, 'success')
    
    return redirect(url_for('order_confirmation', order_id=order.id))

@app.route('/order/confirmation/<int:order_id>')
@login_required
def order_confirmation(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Ensure user owns this order
    if order.user_id != session['user_id']:
        abort(403)
    
    return render_template('order_confirmation.html', order=order)

@app.route('/orders')
@login_required
def orders():
    orders = Order.query.filter_by(user_id=session['user_id']).order_by(Order.created_at.desc()).all()
    return render_template('orders.html', orders=orders)

@app.route('/order/<int:order_id>')
@login_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    
    # Ensure user owns this order
    if order.user_id != session['user_id'] and not session.get('is_admin', False):
        abort(403)
    
    return render_template('order_detail.html', order=order)

@app.route('/address')
@login_required
def addresses():
    addresses = Address.query.filter_by(user_id=session['user_id']).all()
    return render_template('addresses.html', addresses=addresses)

@app.route('/address/add', methods=['GET', 'POST'])
@login_required
def add_address():
    form = AddressForm()
    
    if form.validate_on_submit():
        # Validate pincode
        if not is_valid_pincode(form.pincode.data):
            flash('Invalid PIN code. Please enter a valid Indian PIN code.', 'danger')
            return render_template('address_form.html', form=form, title='Add New Address')
        
        # If setting as default, unset any current default
        if form.is_default.data:
            Address.query.filter_by(user_id=session['user_id'], is_default=True).update({'is_default': False})
        
        # Create new address
        address = Address(
            user_id=session['user_id'],
            address_line1=form.address_line1.data,
            address_line2=form.address_line2.data,
            city=form.city.data,
            state=form.state.data,
            pincode=form.pincode.data,
            phone=form.phone.data,
            is_default=form.is_default.data
        )
        
        db.session.add(address)
        db.session.commit()
        
        flash('Address added successfully', 'success')
        
        # Redirect to next page if provided
        next_page = request.args.get('next')
        if next_page:
            return redirect(next_page)
        return redirect(url_for('addresses'))
    
    return render_template('address_form.html', form=form, title='Add New Address')

@app.route('/address/edit/<int:address_id>', methods=['GET', 'POST'])
@login_required
def edit_address(address_id):
    address = Address.query.get_or_404(address_id)
    
    # Ensure user owns this address
    if address.user_id != session['user_id']:
        abort(403)
    
    form = AddressForm(obj=address)
    
    if form.validate_on_submit():
        # Validate pincode
        if not is_valid_pincode(form.pincode.data):
            flash('Invalid PIN code. Please enter a valid Indian PIN code.', 'danger')
            return render_template('address_form.html', form=form, title='Edit Address')
        
        # If setting as default, unset any current default
        if form.is_default.data and not address.is_default:
            Address.query.filter_by(user_id=session['user_id'], is_default=True).update({'is_default': False})
        
        # Update address
        address.address_line1 = form.address_line1.data
        address.address_line2 = form.address_line2.data
        address.city = form.city.data
        address.state = form.state.data
        address.pincode = form.pincode.data
        address.phone = form.phone.data
        address.is_default = form.is_default.data
        
        db.session.commit()
        
        flash('Address updated successfully', 'success')
        return redirect(url_for('addresses'))
    
    return render_template('address_form.html', form=form, title='Edit Address')

@app.route('/address/delete/<int:address_id>')
@login_required
def delete_address(address_id):
    address = Address.query.get_or_404(address_id)
    
    # Ensure user owns this address
    if address.user_id != session['user_id']:
        abort(403)
    
    # Check if address is used in any orders
    if Order.query.filter_by(address_id=address_id).first():
        flash('Cannot delete this address as it is used in orders', 'danger')
        return redirect(url_for('addresses'))
    
    db.session.delete(address)
    db.session.commit()
    
    flash('Address deleted successfully', 'success')
    return redirect(url_for('addresses'))

@app.route('/pincode/validate', methods=['POST'])
def validate_pincode():
    pincode = request.form.get('pincode')
    is_valid = is_valid_pincode(pincode)
    
    return jsonify({
        'valid': is_valid,
        'message': 'Valid PIN code' if is_valid else 'Invalid PIN code'
    })

# Admin routes
@app.route('/admin')
@admin_required
def admin_dashboard():
    total_products = Product.query.count()
    total_orders = Order.query.count()
    total_users = User.query.filter_by(is_admin=False).count()
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(5).all()
    
    # Calculate revenue
    total_revenue = db.session.query(db.func.sum(Order.total_amount)).scalar() or 0
    
    return render_template('admin/dashboard.html', 
                          total_products=total_products,
                          total_orders=total_orders,
                          total_users=total_users,
                          total_revenue=total_revenue,
                          recent_orders=recent_orders)

@app.route('/admin/products')
@admin_required
def admin_products():
    products = Product.query.all()
    return render_template('admin/products.html', products=products)

@app.route('/admin/product/add', methods=['GET', 'POST'])
@admin_required
def admin_add_product():
    form = ProductForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            description=form.description.data,
            price=form.price.data,
            stock=form.stock.data,
            image_url=form.image_url.data,
            category_id=form.category_id.data,
            featured=form.featured.data
        )
        
        db.session.add(product)
        db.session.commit()
        
        flash('Product added successfully', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/product_form.html', form=form, title='Add New Product')

@app.route('/admin/product/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def admin_edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.all()]
    
    if form.validate_on_submit():
        product.name = form.name.data
        product.description = form.description.data
        product.price = form.price.data
        product.stock = form.stock.data
        product.image_url = form.image_url.data
        product.category_id = form.category_id.data
        product.featured = form.featured.data
        
        db.session.commit()
        
        flash('Product updated successfully', 'success')
        return redirect(url_for('admin_products'))
    
    return render_template('admin/product_form.html', form=form, title='Edit Product')

@app.route('/admin/product/delete/<int:product_id>')
@admin_required
def admin_delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    # Check if product is in any order
    if OrderItem.query.filter_by(product_id=product_id).first():
        flash('Cannot delete this product as it appears in orders', 'danger')
        return redirect(url_for('admin_products'))
    
    # Remove from all carts
    CartItem.query.filter_by(product_id=product_id).delete()
    
    db.session.delete(product)
    db.session.commit()
    
    flash('Product deleted successfully', 'success')
    return redirect(url_for('admin_products'))

@app.route('/admin/orders')
@admin_required
def admin_orders():
    status_filter = request.args.get('status', '')
    
    if status_filter:
        orders = Order.query.filter_by(status=status_filter).order_by(Order.created_at.desc()).all()
    else:
        orders = Order.query.order_by(Order.created_at.desc()).all()
    
    return render_template('admin/orders.html', orders=orders, current_status=status_filter)

@app.route('/admin/order/<int:order_id>')
@admin_required
def admin_order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order)

@app.route('/admin/order/status/<int:order_id>', methods=['POST'])
@admin_required
def admin_update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    status = request.form.get('status')
    
    if status in ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled']:
        order.status = status
        db.session.commit()
        flash(f'Order status updated to {status}', 'success')
    else:
        flash('Invalid status', 'danger')
    
    return redirect(url_for('admin_order_detail', order_id=order_id))

@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/user/<int:user_id>')
@admin_required
def admin_user_detail(user_id):
    user = User.query.get_or_404(user_id)
    orders = Order.query.filter_by(user_id=user_id).order_by(Order.created_at.desc()).all()
    addresses = Address.query.filter_by(user_id=user_id).all()
    
    return render_template('admin/user_detail.html', user=user, orders=orders, addresses=addresses)
