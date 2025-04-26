from app import app, db  # noqa: F401
from models import User
from werkzeug.security import generate_password_hash
from flask import session

# Create admin user if not exists
with app.app_context():
    admin_email = 'admin@example.com'
    admin_user = User.query.filter_by(email=admin_email).first()
    
    if not admin_user:
        hashed_password = generate_password_hash('admin123')
        admin_user = User(
            name='Admin User',
            email=admin_email,
            password=hashed_password,
            is_admin=True
        )
        db.session.add(admin_user)
        db.session.commit()
        print(f"Admin user created with email: {admin_email} and password: admin123")
    else:
        # Ensure user is admin
        if not admin_user.is_admin:
            admin_user.is_admin = True
            db.session.commit()
            print(f"User {admin_email} upgraded to admin")
        print(f"Admin user already exists with email: {admin_email}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
