from flask import Flask,Blueprint, request, jsonify
from sqlalchemy.orm import aliased
from sqlalchemy.sql import case
from flask_jwt_extended import create_access_token,jwt_required,get_jwt_identity,decode_token,verify_jwt_in_request
from src.extensions import db
from src.models import User, Question, Response,Category , RiskProfile,UserRisk,Menu,User_ACL,LoginHistory,Department,Organisation
from datetime import datetime,timedelta
from flask_cors import CORS, cross_origin
from sqlalchemy import func
from sqlalchemy import desc
from werkzeug.security import generate_password_hash
import secrets
from config import RESET_PASS_LINK
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText




app = Flask(__name__)
CORS(app)
#app.register_blueprint(routes)



api_blueprint = Blueprint('api', __name__)
#@api_blueprint.route('/api')
@cross_origin()  # CORS only for this route


# @api_blueprint.before_request
# def log_headers():
#     print(f"Incoming Request: {request.method} {request.url}")
#     print(f"Headers: {request.headers}")


@api_blueprint.route("/api/check_session", methods=["GET"])
@jwt_required()  # Requires a valid token
def check_session():
   
    try:
        user = get_jwt_identity()  # Extract user info from JWT
        return jsonify({"authenticated": True, "user": user}), 200
    except Exception as e:
        return jsonify({"authenticated": False, "error": str(e)}), 401





@api_blueprint.route("/api/departments", methods=["GET"])
def get_departments():
    """Fetch all departments"""
    departments = Department.query.all()
    print(departments)
    return jsonify([{"id": dept.id, "name": dept.name} for dept in departments])



@api_blueprint.route('/api/login', methods=['POST'])
def login():
    data = request.json
    user = User.query.filter_by(email=data["email"]).first()
    message = "Authentication failed. Please try again."
    access_token=None
    try:
        if user:
            if user.status=="active":
                if user.check_password(data["password"]):
                    #token = create_access_token(identity=user.id)
                    access_token = create_access_token(identity=str(user.id))  # Convert ID to STRING
                    login_status = "SUCCESS"
                    #return jsonify({"status":"SUCCESS","access_token":access_token}), 200
                else:
                    login_status = "FAIL"
                    message = "Authentication failed. Invalid Credentials! "
            else:
                login_status = "FAIL"
                message = "Authentication failed.   User is not active ! "
            login_history(request,user,login_status)
        else:
            login_status = "FAIL"
            message = "Authentication failed.  User not found ! "
            #return jsonify({"status":"FAIL","message": "Active User not found ! "}), 400

        
        
        if login_status == "SUCCESS":
            if user.first_login_flag:
                return jsonify({"status": "CHANGE_PASSWORD_REQUIRED", "message": "First login detected. Please change your password.","user_id":user.id})

            return jsonify({"status":"SUCCESS","access_token":access_token,"user_type":user.user_type,"user_fname": user.firstname,"user_lname": user.lastname}), 200
        else:
            return jsonify({"status":"FAIL","message": message}), 400

    except Exception as e:
        return jsonify({"status":"FAIL","error": str(e)}), 500
    
    
def login_history(request,user,login_status):
    try:
        print("inside Login History")
        data=request.json
        user_id = user.id if user else None
        ip_addr = request.remote_addr
        #mac_address = get_mac_address()
        mac_address = None
        user_agent = request.headers.get("User-Agent", "Unknown")
        device_name = data.get("device_name", "Unknown")
        channel = data.get("channel", "Web")  # Web/Mobile/API
        #latitude, longitude = get_user_location()
        latitude, longitude = None,None

        # Save login history using ORM
        login_history = LoginHistory(
            user_id=user_id,
            login_status=login_status,
            ip_addr=ip_addr,
            mac_address=mac_address,
            user_agent=user_agent,
            device_name=device_name,
            channel=channel,
            latitude=latitude,
            longitude=longitude
        )
        print(f"inside Login History {login_history}")
        db.session.add(login_history)
        db.session.commit()

    except Exception as e:
        db.session.rollback()
        print(f"EXCEPTION IS {str(e)}")


@api_blueprint.route("/api/forgot_password", methods=["POST"])
def forgot_password():
    data = request.json
    email = data.get("email")

    user = User.query.filter_by(email=email).first()
    if not user:
        return jsonify({"status": "FAILED", "message": "User not found"}), 404
    username="{user.firstname} {user.lastname}"
    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    user.reset_token = reset_token
    user.reset_token_expiry = datetime.utcnow() + timedelta(minutes=60)

    db.session.commit()

    # Simulate sending email (replace with actual email logic)
    reset_link = f"{RESET_PASS_LINK}{reset_token}"
    print(f"Send this link via email: {reset_link}")
    send_email(email,username,reset_link)
    return jsonify({"status": "SUCCESS", "message": "Password reset link sent to your email."})



@api_blueprint.route("/api/reset_password", methods=["POST"])
def reset_password():
    data = request.json
    token = data.get("token")
    new_password = data.get("new_password")

    user = User.query.filter_by(reset_token=token).first()

    if not user or user.reset_token_expiry < datetime.utcnow():
        return jsonify({"status": "FAILED", "message": "Invalid or expired token"}), 400

    # Update password
    user.password_hash = generate_password_hash(new_password)
    user.reset_token = None  # Clear the token
    user.reset_token_expiry = None

    db.session.commit()

    return jsonify({"status": "SUCCESS", "message": "Password has been reset successfully."})


@api_blueprint.route("/api/change_password", methods=["POST"])
def change_password():

    data = request.json
    user_id = data.get("user_id")
    new_password = data.get("new_password")
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({"status": "FAILED", "message": "User not found"}), 404
    
    # Update password (store hashed password)
    user.password_hash = generate_password_hash(new_password)
    user.first_login_flag = False  # Mark first login as completed

    db.session.commit()
    

    return jsonify({"status": "SUCCESS", "message": "Password changed successfully. You can now log in."})


@api_blueprint.route('/api/get_users', methods=['GET'])
@jwt_required()
def get_users():
    
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', None, type=int)
    print(f"per_page  : {per_page}")
    if per_page is not None: 
        #users = User.query.paginate(page=page, per_page=per_page, error_out=False)
        users = User.query.order_by(User.id).paginate(page=page, per_page=per_page, error_out=False)
        
        
        return jsonify({
            "users": [user.to_dict() for user in users.items],
            "total_pages": users.pages,
            "current_page": users.page
        }), 200
    else:
        #users = User.query.order_by(User.id).all()
        users = User.query.outerjoin(Department).order_by(User.id).all()
        user_list = [
        {
            "id": user.id,
            "firstname": user.firstname,
            "lastname": user.lastname,
            "email": user.email,
            "department_id": user.department_id,
            "department_name": user.department.name if user.department else "N/A",
            "status":user.status,
            "user_type":user.user_type,
            "designation_name":user.designation_name
        }
        for user in users
    ]
      
        return jsonify({
            "users": user_list,
            "total_pages": 0,
            "current_page": 0
        }), 200


# Update user details (PUT)
@api_blueprint.route("/api/users/<int:user_id>", methods=["PUT"])
@jwt_required()
def update_user(user_id):
    data = request.json
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    user.firstname = data.get("firstname", user.firstname)
    user.lastname = data.get("lastname", user.lastname)
    user.email = data.get("email", user.email)
    user.user_type = data.get("user_type", user.user_type)
    user.department_id = data.get("department_id", user.department_id)
  
    db.session.commit()
    return jsonify({"id": user.id, "firstname": user.firstname, "lastname": user.lastname,"email": user.email,"status": user.status,"user_type": user.user_type,"department_id":user.department_id})


@api_blueprint.route('/api/update_user_status', methods=['POST'])
@jwt_required()
def update_user_status():
    data = request.json
    user_id = data.get("user_id")
    new_status = data.get("status")

    if not user_id or not new_status:
        return jsonify({"status": "ERROR", "message": "Invalid request"}), 400

    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        user.status=new_status
        db.session.commit()
        
        return jsonify({"status": "SUCCESS", "message": "User status updated successfully!"})
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "ERROR", "message": str(e)}), 500




def send_email(recepient,name,link):

    # SMTP Configuration
    SMTP_SERVER = "smtp.gmail.com"
    SMTP_PORT = 587
    GMAIL_USER = "e.g.prasanth@gmail.com"
    GMAIL_PASSWORD = "gfhm mhgf rstn kipy"  # Use App Password

    # Email Content
    to_email = recepient
    subject = "Password Reset Email"
    body = "Hi {name}, You recently requested for forgot password option for Admin Portal. \
    Please click on the verify link to  confirm the address belongs to you. \
    {link}\
    If you did not make this change or you believe an unauthorized person has accessed your account, you should contact your adminstrator. \
    Support."

    # Create Message
    msg = MIMEMultipart()
    msg["From"] = GMAIL_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    # Send Email
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Secure the connection
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.sendmail(GMAIL_USER, to_email, msg.as_string())
        server.quit()
        print("✅ Email sent successfully!")
    except Exception as e:
        print(f"❌ Error: {e}")


@api_blueprint.route('/api/categories', defaults={'option': None}, methods=['GET'])
@api_blueprint.route('/api/categories/<string:option>', methods=['GET'])
def categories(option):
    try:
        if option:
            #categories = Category.query.filter_by(status="active").all()  # Fetch only active categories
            categories = Category.query.filter().all()
        else:
            categories = Category.query.filter(Category.status == "active").all()
        category_list = [
            {
                    "id": cat.id,
                    "name": cat.name,
                    "description": cat.description,
                    "status":cat.status,
                    "thumbnail": cat.thumbnail_url,
                    "image": cat.image_url
                }
            for cat in categories
        ]
        return jsonify(category_list), 200
    except Exception as e:
        return jsonify({"status":"FAIL","error": str(e)}), 500


@api_blueprint.route('/api/add_categories', methods=['POST'])
@jwt_required()
def manage_categories():
    if request.method == 'POST':
        data = request.json
        
        created_by = get_jwt_identity()
        category = Category(name=data['name'],description=data['description'],created_by=created_by)
        db.session.add(category)
        db.session.commit()
        return jsonify({"status": "SUCCESS",'message': 'Category added successfully'}), 201
    
    

@api_blueprint.route('/api/update_categories/<int:id>', methods=['PUT', 'POST'])
def update_category(id):
    category = Category.query.get(id)
  
    data = request.json
    if not category:
        print({"status": "FAIL",'message': 'Category not found'})
        return jsonify({"status": "FAIL",'message': 'Category not found'}), 404
    
    if request.method == 'PUT':
        
        category.name = data['name']
        category.description = data['description']
        db.session.commit()
        print({"status": "SUCCESS",'message': 'Category updated successfully'})
        return jsonify({"status": "SUCCESS",'message': 'Category updated successfully'})

    category.status = data['status']
    db.session.commit()
    print({"status": "SUCCESS",'message': 'Category status updated successfully'})
    return jsonify({"status": "SUCCESS",'message': 'Category status updated successfully'})



@api_blueprint.route("/api/paginated_categories", methods=["GET"])
@jwt_required()
def paginated_categories():
    
    page = request.args.get("page", 1, type=int)
    per_page = 5  # Adjust the number of categories per page
    print(f"INSIDE  PAGES........{page} ")

    categories_query = Category.query.order_by(Category.id)
    paginated_categories = categories_query.paginate(page=page, per_page=per_page, error_out=False)
    
    return jsonify({
            "categories": [category.to_dict() for category in paginated_categories.items],
            "totalPages": paginated_categories.pages,
            "current_page": paginated_categories.page

        }),200


@api_blueprint.route("/api/risks", methods=["GET"])
def get_risks():
    risk_profiles = RiskProfile.query.order_by(RiskProfile.score_threshold.desc()).all()
    return jsonify([{"id": risk_profile.id, "name": risk_profile.profile_name ,"description": risk_profile.description, "threshold_score": risk_profile.score_threshold, "status": risk_profile.status,"tags": risk_profile.tags,"risk_Indv":risk_profile.individual_score} for risk_profile in risk_profiles])


@api_blueprint.route('/api/add_risks', methods=['POST'])
@jwt_required()
def manage_risks():
    if request.method == 'POST':
        data = request.json
        risks = RiskProfile(profile_name=data['name'],description=data['description'],tags=data['tags'],score_threshold=data['score_threshold'],individual_score=data['indv_score'])
        db.session.add(risks)
        db.session.commit()
        return jsonify({"status": "SUCCESS",'message': 'Risk Profile added successfully'}), 201
    
    

@api_blueprint.route('/api/update_risks/<int:id>', methods=['PUT', 'POST'])
def update_risk(id):
    risk = RiskProfile.query.get(id)
  
    data = request.json
    if not risk:
        return jsonify({"status": "FAIL",'message': 'Risk not found'}), 404
    
    if request.method == 'PUT':
        
        risk.profile_name = data['name']
        risk.description = data['description']
        risk.score_threshold = data['score']
        risk.tags = data['tags']
        risk.individual_score = data['indv_score']
        db.session.commit()
        
        return jsonify({"status": "SUCCESS",'message': 'Risk Profile updated successfully'})

    risk.status = data['status']
    db.session.commit()
    
    return jsonify({"status": "SUCCESS",'message': 'Category status updated successfully'})


@api_blueprint.route('/api/questions', methods=['GET'])
def get_questions():
   
    category = request.args.get("category_id")
    
    limit = int(request.args.get("limit")) if request.args.get("limit") else 5
   
    if limit and limit != 0:
        questions = Question.query.filter(Question.category_id == category,func.lower(Question.status) == "active").limit(limit).all()
        
    elif limit == 0:
         questions = Question.query.filter(Question.category_id == category).order_by(Question.id).all()
    else:
        questions = Question.query.filter(Question.category_id == category,func.lower(Question.status) == "active").limit(5).all()
       
    if limit==0:
        resp_data=[
            {
                "id": q.id,
                "question_text": q.text,
                "status": q.status,
                "options": [
                    {"option": "option_1","text": q.option_1, "score": q.score_1},
                    {"option": "option_2","text": q.option_2, "score": q.score_2},
                    {"option": "option_3","text": q.option_3, "score": q.score_3},
                    {"option": "option_4","text": q.option_4, "score": q.score_4},
                ]   
            
            }
            for q in questions
        ]
    else:
        resp_data=[
            {
                "id": q.id,
                "question_text": q.text,
                "options": {
                    "option_1": q.option_1,
                    "option_2": q.option_2,
                    "option_3": q.option_3,
                    "option_4": q.option_4
                }
            }
            for q in questions
        ]
    print(resp_data)
    return jsonify({"status":"SUCCESS", "data": resp_data}), 201
    

@api_blueprint.route('/api/edit_answers/<int:id>', methods=['POST'])
def edit_answers(id):
   
    data = request.json
    question = Question.query.get(id)
    
    if not question:
        return jsonify({"status": "FAIL", "message": "Question not found"}), 404
    
    if hasattr(Question, data["option"]):
        setattr(question, data["option"] , data["text"])  # Dynamically set column value
        db.session.commit()
        return jsonify({"status": "SUCCESS", "message": "Question updated successfully"})
    else:
        return jsonify({"status": "FAIL", "message": "Question not found"}), 404

    
@api_blueprint.route('/api/edit_questions/<int:id>', methods=['POST','DELETE'])
def edit_questions(id):
    try:
        data = request.json
        new_status=data.get("status")
        question = Question.query.get(id)
        if not question:
            return jsonify({"status": "FAIL", "message": "Question not found"}), 404
        if request.method == 'DELETE':
            question.status = new_status
            db.session.commit() 
            return jsonify({"status": "SUCCESS", "message": "Question deleted successfully"})
        else:
            question.text = data["text"]
            question.category_id = data["new_category_id"]
            db.session.commit()        
            return jsonify({"status": "SUCCESS", "message": "Question updated successfully"})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "FAIL", "message": str(e)}), 500
        



@api_blueprint.route('/api/submit-responses', methods=['POST'])
def submit_responses():
    
    """
    API to handle multiple question responses from the user.
    It fetches the actual score from the questions table, calculates total score,
    determines the user's risk profile, and stores it in user_risk table.
    """
    try:
        data = request.json
        category_id=None
        # Extract common fields
        user_id = data.get("user_id")
        source = data.get("source")  # "Web" or "Mobile"
        source = source.lower() if source else None
        stage = data.get("stage")  # Optional
        dob = data.get("dob")  # Optional, format: YYYY-MM-DD
        responses = data.get("responses", [])  # List of responses
        
        if not user_id or not source or not responses:
            return jsonify({"status":"FAIL","error": "Missing required fields"}), 400
       
        total_score = 0

        for response in responses:
           
            question_id = response.get("question_id")
            selected_option = response.get("selected_option")
            
            if not question_id or selected_option is None:
                return jsonify({"status":"FAIL","error": "Invalid response data"}), 400
            

            # Fetch the question from the database
            question = Question.query.get(question_id)
            #question=Question.query.filter_by(id=question_id).first()
            
            if not question:
                return jsonify({"status":"FAIL","error": f"Question ID {question_id} not found"}), 404
        
            # Dynamically fetch the score based on selected option
            if selected_option == "option_1":
                score = question.score_1
            elif selected_option == "option_2":
                score = question.score_2
            elif selected_option == "option_3":
                score = question.score_3
            elif selected_option == "option_4":
                score = question.score_4
            else:
                return jsonify({"status":"FAIL","error": f"Invalid option selected for Question ID {question_id}"}), 400

            total_score += score
            category_id=question.category_id
            # Save the individual response
            new_response = Response(
                user_id=user_id,
                question_id=question_id,
                selected_option=selected_option,
                channel=source,
                stage=stage,
                dob=datetime.strptime(dob, "%Y-%m-%d") if dob else None,
                created_at=datetime.utcnow()
            )
            db.session.add(new_response)
            db.session.commit()
            db.session.flush()
       
        # Fetch the appropriate risk profile based on total score
        risk_profile = RiskProfile.query.filter(RiskProfile.score_threshold <= total_score)\
                                        .order_by(RiskProfile.score_threshold.desc()).first()
        
        if not risk_profile:
            return jsonify({"status":"FAIL","error": "No matching risk profile found"}), 400

        # Mark previous risk profiles for the user as inactive
        UserRisk.query.filter_by(user_id=user_id, status="active").update({"status": "inactive"})

        # Store the new risk profile in user_risk table
        new_user_risk = UserRisk(
            user_id=user_id,
            risk_profile_id=risk_profile.id,
            risk_profile_name=risk_profile.profile_name,
            risk_score=total_score,
            status="active",
            channel=source,
            category_id=category_id,
            created_at=datetime.utcnow()
        )
        db.session.add(new_user_risk)
        db.session.commit()
     
        return jsonify({"status":"SUCCESS","message": "Responses submitted successfully", "user_id":user_id, "risk_profile": risk_profile.profile_name,"tags":risk_profile.tags}), 201

    except Exception as e:
        db.session.rollback()
        print(f"Exception occured {str(e)}")
        return jsonify({"status":"FAIL","error": str(e)}), 500



@api_blueprint.route('/api/user_risk_validate', methods=['PATCH'])
def validate_user_risk():
    """
    API to update user validation feedback for their risk profile.
    """
    print("INSIDE VALIDATE")
    data = request.json
    user_id = data.get("user_id")
    validation = data.get("validation")  # "Accepted" or "Rejected"
    
    if not user_id:
        return jsonify({"status":"FAIL","error": "Invalid input"}), 400

    # Find the ACTIVE risk profile for the user
    user_risk = UserRisk.query.filter_by(user_id=user_id, status="active").first()
    if not user_risk:
        return jsonify({"status":"FAIL","error": "No active risk profile found for user"}), 404

    # Update validation fields
    user_risk.user_stars = validation
    user_risk.validated_at = datetime.utcnow()

    db.session.commit()
    return jsonify({"status":"SUCCESS","message": "User risk profile validated successfully"}), 200
    try: 
        print("INSIDE VALIDATE")
    except Exception as e:
        db.session.rollback()
        return jsonify({"status":"FAIL","error": str(e)}), 500


@api_blueprint.route('/api/fetch_profile', methods=['POST'])
def fetch_profile():
    """
    API to fetch risk profile for user .
    """
    try:
        data = request.json
        user_id = data.get("user_id")
    
        # Find the ACTIVE risk profile for the user
        user_risk = UserRisk.query.filter_by(user_id=user_id, status="active").first()
        if not user_risk:
            return jsonify({"status":"FAIL","message": "No active risk profile found for user"}), 404
        return jsonify({"status":"SUCCESS","user_risk_segment":user_risk.risk_profile_name,"risk_id":user_risk.risk_profile_id}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({"status":"FAIL", "message": str(e)}), 500



@api_blueprint.route('/api/risk_profiles', methods=['GET'])
@jwt_required()
def get_risk_profiles():
    print("INSIDE RISK PROFILES........")
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 5, type=int)
    
    risk_profiles_query = RiskProfile.query.order_by(RiskProfile.score_threshold.desc())
    risk_profiles_rows=risk_profiles_query.paginate(page=page, per_page=per_page, error_out=False)
    risk_profiles = risk_profiles_rows.items

    return jsonify({
        "risk_profiles": [rp.to_dict() for rp in risk_profiles],
        "total_pages": risk_profiles_rows.pages,
        "current_page": page
    })

@api_blueprint.route('/api/result_summary', methods=['POST'])
def get_result_summary():
    print("INSIDE RISK PROFILES........")
    
   
    data = request.json
    user_id = data.get("user_id")
    q = aliased(Question)

    # Mapping selected option to corresponding score

    selected_option_value = case(
        (Response.selected_option == "option_1", q.option_1),
        (Response.selected_option == "option_2", q.option_2),
        (Response.selected_option == "option_3", q.option_3),
        (Response.selected_option == "option_4", q.option_4),
        else_=None
    ).label("selected_option_value")

    # Define a case statement to dynamically select the score based on selected option
    selected_score = case(
        (Response.selected_option == "option_1", q.score_1),
        (Response.selected_option == "option_2", q.score_2),
        (Response.selected_option == "option_3", q.score_3),
        (Response.selected_option == "option_4", q.score_4),
        else_=None
    ).label("selected_score")

    results = (
        db.session.query(
            Response.user_id,
            Response.question_id,
            q.text,
            Response.selected_option,
            selected_option_value,
            selected_score
        )
        .join(q, Response.question_id == q.id)
        .filter(Response.user_id == user_id)
        .order_by(desc(Response.id))  # Sort by latest response
        .limit(5)  # Fetch last 5 responses
        .all()
    )
    print(f"RESULTS ARE {results}")
    

    response_data = [
        {
            "user_id": row.user_id,
            "question_id": row.question_id,
            "question_text": row.text,
            "selected_option": row.selected_option,
            "selected_option_value": row.selected_option_value,
            "selected_score": row.selected_score
        }
        for row in results
    ]
    # Find the ACTIVE risk profile for the user
    risk_profile = RiskProfile.query.filter_by(status="active").all()
    if not risk_profile:
        return jsonify({"status":"FAIL","message": "No active risk profile found for user"}), 404

    risk_profiles = [
            {
                    "id": risk.id,
                    "name": risk.profile_name,
                    "description": risk.description,
                    "score_threshold":risk.score_threshold
        
                }
            for risk in risk_profile
        ] 
    print(f"RESULTS ARE {risk_profiles}")
    return jsonify({"status":"SUCCESS","results_data":response_data,"risk_profile":risk_profiles}), 200
    try:
        print(f"RESULTS ARE {risk_profiles}")
    except Exception as e:
        db.session.rollback()
        return jsonify({"status":"FAIL", "message": str(e)}), 500
    

@api_blueprint.route('/api/menus', methods=['GET'])
@jwt_required()
def get_menus():
    menus_list=[]
    try:
        user_id = get_jwt_identity()  # Get user ID from JWT token
    
        # Find the ACTIVE risk profile for the user
        user = User.query.filter_by(id=user_id).first()
    
        if user:
            if user.user_type=="MEMBER":
                user_menus = (
                    db.session.query(Menu.menu_name)
                    .join(User_ACL, Menu.id == User_ACL.menu_id)
                    .filter(User_ACL.user_id == user_id, User_ACL.access_flag == "Y")
                    .all()
                )
            
                if user_menus and len(user_menus)>0:
                # Convert query result to a list of dictionaries
                    menus_list = [{"menu_name": menu.menu_name} for menu in user_menus]
                return jsonify({"status":"SUCCESS","user_type": "MEMBER","message": "SHOW SELECTED MENUS","menus": menus_list}) ,200
            else:
                return jsonify({"status":"SUCCESS","user_type": "ADMIN","message": "SHOW ALL MENUS","menus": menus_list}), 200
            
        return jsonify({"status":"FAIL","user_type": "","message": ""}), 404
   
    except Exception as e:
        db.session.rollback()
        return jsonify({"status":"FAIL","error": str(e)}), 500


@api_blueprint.route('/api/add_user', methods=['POST'])
@jwt_required()
def add_user():
    
    data = request.get_json()
    firstname = data.get('firstname')
    lastname = data.get('lastname')
    email = data.get('new_val1')
    user_type = data.get('user_type')
    password = data.get('new_val2')
    department_id = data.get('department_id')
    

    if not firstname or not lastname or not email or not user_type:
        return jsonify({"status": "ERROR", "message": "All fields are required"}), 400

    hashed_password = generate_password_hash(password)

    # Get the logged-in user's ID
    created_by = get_jwt_identity()
    print(f" DATA IS {data}")
    # Create a new user
    new_user = User(
        firstname=firstname,
        lastname=lastname,
        email=email,
        password_hash=hashed_password,
        department_id= department_id,
        user_type=user_type,
        status="active",
        created_by=created_by
    )
    db.session.add(new_user)
    db.session.commit()

    # If user is a MEMBER, add ACL records
    if user_type == "MEMBER":
        menu_ids = [menu.id for menu in Menu.query.filter_by(mem_default='Y').all()]
        for menu_id in menu_ids:
            user_acl_entry = User_ACL(user_id=new_user.id, menu_id=menu_id, access_flag="Y")
            db.session.add(user_acl_entry)

    db.session.commit()
    print(f" RESP IS SUCCESS")
    return jsonify({"status": "SUCCESS", "message": "User added successfully"}), 201
    try:
        print("aaa")
    except Exception as e:
        db.session.rollback()
        return jsonify({"status": "ERROR", "message": str(e)}), 500


@api_blueprint.route('/api/add_question', methods=['PUT'])
@jwt_required()
def add_question():
    #try:
    created_by = get_jwt_identity()
    data = request.json
    category_id = int(data["category_id"])
    question_text = data["question_text"]
    answers = data["answers"]

    # Ensure exactly 4 answers are provided
    while len(answers) < 4:
        answers.append({"text": None, "risk_score": None})  # Fill missing options with None

    # Create a new question entry
    new_question = Question(
        category_id=category_id,
        text=question_text,
        option_1=answers[0]["text"],
        option_2=answers[1]["text"],
        option_3=answers[2]["text"],
        option_4=answers[3]["text"],
        score_1=int(answers[0]["risk_score"]) if answers[0]["risk_score"] else None,
        score_2=int(answers[1]["risk_score"]) if answers[1]["risk_score"] else None,
        score_3=int(answers[2]["risk_score"]) if answers[2]["risk_score"] else None,
        score_4=int(answers[3]["risk_score"]) if answers[3]["risk_score"] else None,
        created_by=created_by
    )

    # Add to the session and commit
    db.session.add(new_question)
    db.session.commit()

    return {"message": "Question added successfully", "question_id": new_question.id}
    try:
        print("a")
    except Exception as e:
        db.session.rollback()
        return {"error": str(e)}

@api_blueprint.route('/api/report/risk-classification', methods=['GET'])
def get_risk_classification():
    data = (
        db.session.query(
            UserRisk.risk_profile_id,
            RiskProfile.profile_name,  # Get the profile name from RiskProfile model
            db.func.count(UserRisk.id)
        )
        .join(RiskProfile, UserRisk.risk_profile_id == RiskProfile.id)  # Join UserRisk with RiskProfile
        .group_by(UserRisk.risk_profile_id, RiskProfile.profile_name)
        .all()
    )

    return jsonify([
        {
            "risk_profile_id": row[0],  
            "risk_profile_name": row[1],  # Include the profile name
            "count": row[2]
        }
        for row in data
    ])

# API for Star Rating Report
@api_blueprint.route('/api/report/star-ratings', methods=['GET'])
def get_star_ratings():
    data = UserRisk.query.with_entities(UserRisk.user_stars, db.func.count(UserRisk.id)).group_by(UserRisk.user_stars).order_by(UserRisk.user_stars).all()
    return jsonify([{ "rating": row[0], "count": row[1]} for row in data])

# API for API Call Report
@api_blueprint.route('/api/report/api-calls', methods=['GET'])
def get_api_calls():
    data = UserRisk.query.with_entities(UserRisk.channel, db.func.count(UserRisk.id)).group_by(UserRisk.channel).all()
    return jsonify([{ "channel": row[0], "count": row[1]} for row in data])

# API for Most Preferred Category
@api_blueprint.route('/api/report/preferred-category', methods=['GET'])
def get_preferred_category():
    data = (
        db.session.query(
            Category.name,  # Get the profile name from RiskProfile model
            db.func.count(UserRisk.id)
        )
        .join(Category, UserRisk.category_id == Category.id)  # Join UserRisk with RiskProfile
        .group_by(UserRisk.category_id, Category.name)
        .all()
    )

    return jsonify([
        {
            "category": row[0],  # Include the profile name
            "count": row[1]
        }
        for row in data
    ])
    

@api_blueprint.route('/api/org_create', methods=['POST'])
def org_create():
    data = request.json
    org_name=data.get("name")
    portal_name = data.get("portal_name",org_name)
    website_url = data.get("website_url","")
    mail_server = data.get("mail_server","")
    mail_port = data.get("mail_port",0)       
    username = data.get("username","")
    password_hash = data.get("password_hash","")
    smtp_server = data.get("smtp_server","")       
    
    new_company = Organisation(org_name=org_name, portal_name=portal_name , website_url=website_url,mail_server=mail_server,mail_port=mail_port,username=username,password_hash=password_hash,smtp_server=smtp_server)
    db.session.add(new_company)
    db.session.commit()

    return jsonify({"message": "Logo uploaded successfully"}), 201

@api_blueprint.route('/api/get_organization', methods=['GET'])
def get_organization():
    orgs = Organisation.query.filter_by().all()
    if orgs:
        return jsonify([{"name": org.org_name, "portal_name": org.portal_name} for org in orgs]),201 
        
    return jsonify({"error": "Organization not found"}), 404

@api_blueprint.route("/api/user_emails", methods=["GET"])
def get_emails():
    users = User.query.all()
    return jsonify([{"id": user.id, "email": user.email} for user in users])

@api_blueprint.route("/api/manage_user_acl", methods=["POST"])
def get_user_acl():
    data = request.json
    user_email = data.get("user_id")
    user = User.query.filter_by(email=user_email).first()
 
    acl_entries = (
        db.session.query(User_ACL.menu_id, Menu.menu_name,User_ACL.access_flag)
        .join(Menu, User_ACL.menu_id == Menu.id)  # Join with Menus table
        .filter(User_ACL.user_id == user.id)  # Filter by user_id
        .all()
    )
    
        
    return jsonify([{"id": row.menu_id, "menu_name": row.menu_name , "access": row.access_flag} for row in acl_entries])
   
 
@api_blueprint.route("/api/get_org", methods=["GET"])
def get_org():
    
    org=Organisation.query.order_by(Organisation.id.desc()).first()
    if org:
        return jsonify({"id": org.id, "portal_name": org.portal_name}),201 
        
    return jsonify({"error": "Organization not found"}), 404

@api_blueprint.route("/api/edit_organization", methods=["PUT"])
def update_organization():
    data = request.json
    org = Organisation.query.first()
    if org:
        org.org_name = data.get("org_name", org.name)
        org.portal_name = data.get("portal_name", org.portal_name)
        org.email = data.get("email", org.email)
        org.status = data.get("status", org.active)
        db.session.commit()
        return jsonify({"message": "Organization updated"})
    return jsonify({"error": "Organization not found"}), 404

if __name__ == "__main__":
    app.run(debug=True)