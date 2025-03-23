import uuid
from datetime import datetime
from src.extensions import db
from werkzeug.security import generate_password_hash, check_password_hash




# Users Model

class Department(db.Model):
    __tablename__ = "department"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(20), default="active", nullable=False)  # ACTIVE/INACTIVE
    
   


    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at,
            "status": self.status,
        }


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    firstname = db.Column(db.String(50))
    lastname = db.Column(db.String(50))
    password_hash = db.Column(db.String(255), nullable=False)  # Stores hashed passwords
    status = db.Column(db.String(20), default="active", nullable=False)  # ACTIVE/INACTIVE
    department_id=db.Column(db.Integer,  db.ForeignKey("department.id", ondelete="CASCADE"), nullable=False)
    designation_name = db.Column(db.String(50))
    first_login_flag=db.Column(db.Boolean, default=True)  # Track first login
    user_type = db.Column(db.String(20), default="MEMBER", nullable=False)  # ADMIN/MEMBER
    created_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.Integer)  # ADMIN/MEMBER
    reset_token = db.Column(db.String(100), unique=True, nullable=True)
    reset_token_expiry = db.Column(db.DateTime, nullable=True)

    department = db.relationship("Department", backref="users")
    

    def set_password(self, password):
        """Hash and store password securely"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Compare plaintext password with stored hash"""
        return check_password_hash(self.password_hash, password)


    def to_dict(self):
        return {
            "id": self.id,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "email": self.email,
            "status": self.status,
            "user_type": self.user_type,
            "designation_name": self.designation_name,
            "created_by":self.created_by,
            "first_login_flag": self.first_login_flag,
            "department_id": self.department_id
            
        }



class LoginHistory(db.Model):
    __tablename__ = "login_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    accessed_at = db.Column(db.DateTime, default=datetime.utcnow)
    login_status = db.Column(db.String(20), nullable=False)
    latitude = db.Column(db.Numeric(9, 6), nullable=True)
    longitude = db.Column(db.Numeric(9, 6), nullable=True)
    ip_addr = db.Column(db.String(45), nullable=False)  # Supports both IPv4 & IPv6
    channel = db.Column(db.String(20), nullable=True)
    device_name = db.Column(db.String(255), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)
    mac_address = db.Column(db.String(20), nullable=True)

    def __repr__(self):
        return f"<LoginHistory user_id={self.user_id} status={self.login_status} ip={self.ip_addr}>"


# Categories Model (New)
class Category(db.Model):
    __tablename__ = "categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(10), default="active", nullable=False)  # ACTIVE/INACTIVE
    thumbnail_url = db.Column(db.Text, nullable=True)  # Thumbnail image URL
    image_url = db.Column(db.Text, nullable=True)  # Full-size image URL
    created_by = db.Column(db.Integer, nullable=False)  # User ID of creator
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    #questions = db.relationship('Question', backref='category', lazy=True)
    questions = db.relationship('Question', back_populates='category_rel', lazy=True)

    def deactivate_category(category_id):
        category = Category.query.get(category_id)
        if category:
            category.status = "inactive"
            db.session.commit()
            print(f"✅ Category {category_id} deactivated")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "created_by" : self.created_by
           
        }


class Question(db.Model):
    __tablename__ = "questions"
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    text = db.Column(db.String(255), nullable=False)
    option_1 = db.Column(db.String(255), nullable=False)
    option_2 = db.Column(db.String(255), nullable=False)
    option_3 = db.Column(db.String(255), nullable=False)
    option_4 = db.Column(db.String(255), nullable=False)
    score_1 = db.Column(db.Integer, nullable=False)
    score_2 = db.Column(db.Integer, nullable=False)
    score_3 = db.Column(db.Integer, nullable=False)
    score_4 = db.Column(db.Integer, nullable=False)
    
    status = db.Column(db.String(10), default="active", nullable=False)  # ACTIVE/INACTIVE
    created_by = db.Column(db.Integer, nullable=False)  # User ID of creator
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    #category = db.relationship('Category', backref=db.backref('questions', lazy=True))
    category_rel = db.relationship('Category', back_populates='questions')


# Responses Model (Updated)
    

class Response(db.Model):
    __tablename__ = "responses"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(255), nullable=False)  # Frontend-generated unique ID
    question_id = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    selected_option = db.Column(db.String(30), nullable=False)  # Selected option (1-4)
    channel = db.Column(db.String(10), nullable=False)  # Mobile/Web
    stage = db.Column(db.String(30), nullable=True)  # Optional
    dob = db.Column(db.Date, nullable=True)  # Optional Date of Birth
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Response {self.user_id} - Q{self.question_id} - Option {self.selected_option}>"

    def add_response(user_id, question_id, selected_option, channel, stage=None,dob=None):
        new_response = Response(
            user_id=user_id,  # Not necessarily unique
            question_id=question_id,
            selected_option=selected_option,
            channel=channel,
            stage=stage,
            dob=dob
        )
        db.session.add(new_response)
        db.session.commit()
        print("✅ Response recorded successfully")

class RiskProfile(db.Model):
    __tablename__ = "risk_profiles"
    id = db.Column(db.Integer, primary_key=True)
    profile_name = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    score_threshold = db.Column(db.Integer, nullable=False)  # % Score threshold (0-100)
    tags = db.Column(db.Text, nullable=True)  # Can store comma-separated tags or JSON list
    status = db.Column(db.String(10), nullable=False, default='active')  # Active/Inactive
    individual_score = db.Column(db.Integer, nullable=False) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<RiskProfile {self.profile_name} - {self.score_threshold}%>"

    def set_tags(self, tag_list):
        """Store tags as a JSON string"""
        self.tags = json.dumps(tag_list)

    def get_tags(self):
        """Retrieve tags as a list"""
        return json.loads(self.tags) if self.tags else []

    def to_dict(self):
        return {
            "id": self.id,
            "profile_name": self.profile_name,
            "description": self.description,
            "score_threshold": self.score_threshold,
            "tags": self.tags.split(",") if self.tags else [],
            "status": self.status,
            "individual_score" : self.individual_score
        }


class UserRisk(db.Model):
    __tablename__ = "user_risk"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(255), nullable=False)  # Frontend-generated unique ID
    risk_profile_id = db.Column(db.Integer, db.ForeignKey('risk_profiles.id'), nullable=False)
    risk_profile_name = db.Column(db.String(255), nullable=False)  # Derived from RiskProfile
    risk_score = db.Column(db.Integer, nullable=False)  # Total score (0-100)
    channel = db.Column(db.String(10), nullable=False)  # Mobile/Web
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    status = db.Column(db.String(10), nullable=False, default='active')  # Active/Inactive
    user_stars=db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_validation = db.Column(db.String(20), nullable=True) 
    validated_at = db.Column(db.DateTime, nullable=True)
        
    risk_profile = db.relationship("RiskProfile", backref="user_risk")
    category = db.relationship("Category", backref="user_risk")

    def __repr__(self):
        return f"<UserRisk {self.user_id} - {self.risk_profile_name} ({self.risk_score}%)>"

class Menu(db.Model):
    __tablename__ = "menus"
    id = db.Column(db.Integer, primary_key=True)
    menu_name = db.Column(db.String(10), nullable=False)
    menu_description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(10), nullable=False, default='active')  # Active/Inactive
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    mem_default = db.Column(db.String(5), nullable=False,default='N')

    def to_dict(self):
        return {
            "id": self.id,
            "menu_name": self.menu_name,
            "menu_description": self.menu_description,
            "status": self.status,
            "mem_default" : self.mem_default
        }
    
class User_ACL(db.Model):
    __tablename__ = "user_acl"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    menu_id = db.Column(db.Integer, db.ForeignKey('menus.id'),nullable=False)
    access_flag = db.Column(db.String(10), nullable=False,default='Y')
    created_at= db.Column(db.DateTime, default=datetime.utcnow)
    menu = db.relationship("Menu", backref="user_access")
    
    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "menu_id": self.menu_id,
            "access_flag": self.access_flag
        
        }


class Organisation(db.Model):
    __tablename__ = "organisation"
    id = db.Column(db.Integer, primary_key=True)
    org_name = db.Column(db.String(100))
    portal_name = db.Column(db.String(100))
    logo =db.Column(db.String(255))
    website_url = db.Column(db.String(255))
    mail_server = db.Column(db.String(255))
    mail_port = db.Column(db.Integer)
    username = db.Column(db.String(100))
    password_hash = db.Column(db.String(100))
    smtp_server = db.Column(db.String(100))
    status = db.Column(db.String(10), nullable=False, default='active')  # Active/Inactive
    created_at= db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "org_name": self.org_name,
            "portal_name": self.portal_name,
            "logo": self.logo,
            "website_url": self.website_url,
            "mail_server": self.mail_server,
            "mail_port": self.mail_port,
            "username": self.username,
            "password_hash": self.password_hash,
            "smtp_server": self.smtp_server,
            "status": self.status
        }   