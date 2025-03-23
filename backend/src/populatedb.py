from src.app import app, db
from src.models import User, Category, Question, RiskProfile
from werkzeug.security import generate_password_hash
import json

def populate_default_data():
    """Populates the database with default Users, Categories, and Questions."""

    # Ensure fresh start
    db.session.rollback()
    department=[
        Department(name="GEN IT ADMIN", description="Admin Department",status="active")),
    ]
    # ✅ Insert Default Users (with Hashed Passwords)
    users = [
        User(email="admin@pragmaticdigital.in", password_hash=generate_password_hash("Admin123"),departmen_id=1),
        User(email="user1@example.com", password_hash=generate_password_hash("password1"),department_id=1)
    ]

    # ✅ Insert Default Categories
    categories = [
        Category(name="Capital Market",description="Questions related to stock market investments",status="active",thumbnail_url="https://example.com/thumbnails/capital_market.png",image_url="https://example.com/images/capital_market.jpg",created_by=1),
        Category(name="Travel",description="Questions related to Travel ",status="active",thumbnail_url="https://example.com/thumbnails/capital_market.png",image_url="https://example.com/images/capital_market.jpg",created_by=1),
        Category(name="Cricket",description="Questions related to Cricket",status="active",thumbnail_url="https://example.com/thumbnails/capital_market.png",image_url="https://example.com/images/capital_market.jpg",created_by=1),
    ]

    # ✅ Insert Default Questions (mapped to Categories)
    questions = [
        Question(
            category_id=1, text="How do you react to market fluctuations?",
            option_1="Panic", option_2="Cautious", option_3="Confident", option_4="Aggressive",
            score_1=1, score_2=2, score_3=4, score_4=5,status="active",created_by=1 
        ),
        Question(
            category_id=1, text="How frequently do you invest?",
            option_1="Rarely", option_2="Occasionally", option_3="Regularly", option_4="Always",
            score_1=1, score_2=2, score_3=4, score_4=5,status="active",created_by=1 
        ),
        Question(
            category_id=2, text="Preferred travel type?",
            option_1="Luxury", option_2="Backpacking", option_3="Business", option_4="Adventure",
            score_1=1, score_2=2, score_3=4, score_4=5,status="active",created_by=1 
        )
    ]

    profiles = [
        RiskProfile(profile_name="Extremely Aggressive", description="Highest risk tolerance",
                    score_threshold=90, individual_score=20,tags=json.dumps(["high-risk", "stocks", "trading", "leverage"])),
        RiskProfile(profile_name="Aggressive", description="Above-average risk tolerance",
                    score_threshold=75,individual_score=15, tags=json.dumps(["growth", "equity", "options"])),
        RiskProfile(profile_name="Moderate", description="Medium risk tolerance",
                    score_threshold=50,individual_score=10, tags=json.dumps(["mutual funds", "balanced", "ETF"])),
        RiskProfile(profile_name="Conservative", description="Low risk tolerance",
                    score_threshold=25,individual_score=5, tags=json.dumps(["bonds", "fixed income", "low risk"])),
        RiskProfile(profile_name="Extremely Conservative", description="Minimal risk tolerance",
                    score_threshold=10, individual_score=2, tags=json.dumps(["cash", "deposits", "stable"])),
    ]

    menus = [
        Menu(name="Users",description="User Management",status="active"),
        Menu(name="Categories",description="Category Management ",status="active"),
        Menu(name="Risk Profiles",description="Risk Profile Management",status="active"),
        Menu(name="Test Options",description="Test Strategy ",status="active"),
        Menu(name="Reports",description=" Manage Reports ",status="active"),
        Menu(name="Settings",description="Settings & Setup ",status="active")
        
    ]

    try:
        # Add data to session
        db.session.add_all(department)
        db.session.add_all(users)
        db.session.add_all(categories)
        db.session.add_all(questions)            
        db.session.add_all(profiles)
        db.session.add_all(menus)
        


        # Commit changes
        db.session.commit()
        

    except Exception as e:
        db.session.rollback()
        print(f"❌ Error populating database: {e}")

if __name__ == "__main__":
    #with db.app.app_context():  # Ensure proper context
    #    populate_default_data()

    with app.app_context():  # Use app.app_context() instead of db.app
    # Your database operations
        populate_default_data()   

        
