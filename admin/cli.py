import secrets
import hashlib
from sqlalchemy.orm import Session
from database import SessionLocal
from models import AdminToken

def generate_password():
    """Generate a new admin token and store its hash in the database."""
    # Generate a random 64-character token
    token = secrets.token_urlsafe(48)
    
    # Create hash of the token
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    # Get database session
    db = SessionLocal()
    try:
        # Delete any existing tokens (auto-revocation)
        db.query(AdminToken).delete()
        
        # Create new token record
        admin_token = AdminToken(token_hash=token_hash)
        db.add(admin_token)
        db.commit()
        
        # Print the token (will only be shown once)
        print("\nNew admin token generated successfully!")
        print("IMPORTANT: Save this token now. It will not be shown again.")
        print("\nToken:", token)
        print("\nUse this token to log in to the admin interface.")
        
    finally:
        db.close()

if __name__ == "__main__":
    generate_password() 