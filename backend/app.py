from flask import Flask, jsonify, request, render_template, send_from_directory, redirect, url_for, session
from dotenv import load_dotenv
from flask_cors import CORS
from flask_dance.contrib.azure import make_azure_blueprint
from datetime import datetime, timedelta
import uuid
import json
import os
import requests
import logging
from faculty.routes import faculty_bp

# Add logging configuration
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
app = Flask(__name__,
           template_folder=os.path.join(BASE_DIR, 'frontend/static/templates'),
           static_folder=os.path.join(BASE_DIR, 'frontend/static'))

# Load environment variables
load_dotenv()

app.secret_key = os.getenv("SECRET_KEY")

# Route to add user
@app.route("/add_user", methods=["POST"])
def add_user_route():
    data = request.get_json()
    name = data.get("name")
    email = data.get("email")
    
    if not name or not email:
        return jsonify({"error": "Missing name or email"}), 400

    result = add_user(name, email)
    return jsonify({"message": result})

# Route to get users
@app.route("/get_users", methods=["GET"])
def get_users():
    users_ref = db.collection("users").stream()
    users = [{doc.id: doc.to_dict()} for doc in users_ref]
    return jsonify(users)

# Hugging Face API Setup
HUGGINGFACE_API_TOKEN = os.getenv("HUGGINGFACE_API_TOKEN")
MODEL_NAME = os.getenv("MODEL_NAME", "llama3")

HEADERS = {
    "Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}",
    "Content-Type": "application/json"
}

ENDPOINT = f"https://api-inference.huggingface.co/models/tiiuae/falcon-7b-instruct"

# Security headers middleware
@app.after_request
def add_security_headers(response):
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

# Microsoft OAuth Configuration
app.config["AZURE_OAUTH_CLIENT_ID"] = os.getenv("AZURE_OAUTH_CLIENT_ID")
app.config["AZURE_OAUTH_CLIENT_SECRET"] = os.getenv("AZURE_OAUTH_CLIENT_SECRET")
app.config["AZURE_OAUTH_TENANT"] = os.getenv("AZURE_OAUTH_TENANT")
app.config["OAUTHLIB_INSECURE_TRANSPORT"] = os.getenv("OAUTHLIB_INSECURE_TRANSPORT", "0")

azure_bp = make_azure_blueprint(
    client_id=app.config["AZURE_OAUTH_CLIENT_ID"],
    client_secret=app.config["AZURE_OAUTH_CLIENT_SECRET"],
    tenant=app.config["AZURE_OAUTH_TENANT"],
    redirect_to="auth_callback"
)
app.register_blueprint(azure_bp, url_prefix="/login")

# Register faculty blueprint before CORS
app.register_blueprint(faculty_bp, url_prefix='/api/faculty')

CORS(app)

# Ensure the static folder exists
if not os.path.exists('static'):
    os.makedirs('static')

# Load knowledge base
def load_knowledge_base():
    try:
        with open('knowledge_base.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        # Create a sample knowledge base if it doesn't exist
        sample_data = {
            "faculty": [
                {
                    "name": "Dr. Rajesh Kumar",
                    "department": "Computer Science",
                    "designation": "Professor",
                    "email": "rajesh.kumar@upes.ac.in",
                    "specialization": "Artificial Intelligence"
                }
            ],
            "services": [
                {
                    "name": "Library",
                    "location": "Academic Block A",
                    "timing": "9:00 AM - 6:00 PM",
                    "description": "State-of-the-art library with digital resources"
                }
            ],
            "faqs": [
                {
                    "question": "What are the admission requirements?",
                    "answer": "Admission requirements vary by program. Please check the specific program page for detailed requirements."
                }
            ],
            "announcements": [
                {
                    "title": "Semester Registration",
                    "date": "2024-02-17",
                    "content": "Registration for Spring 2024 semester begins next week"
                }
            ]
        }
        with open('knowledge_base.json', 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, indent=4)
        return sample_data

knowledge_base = load_knowledge_base()

@app.route('/')
def root():
    return render_template("caiindex.html")

# Remove the /login route since we're using a modal now
# @app.route('/login')
# def login():
#     return render_template("login.html")

@app.route('/auth/login')
def auth_login():
    # Get login type from query parameter
    login_type = request.args.get('type', 'student')
    session['login_type'] = login_type
    
    # Redirect to Microsoft login
    return redirect(url_for("azure.login"))

@app.route('/auth/callback')
def auth_callback():
    if not azure_bp.session.authorized:
        return redirect(url_for("root"))
        
    resp = azure_bp.session.get("/v1.0/me")
    if not resp.ok:
        return "Authentication failed", 400

    user_data = resp.json()
    email = user_data.get("mail") or user_data.get("userPrincipalName")
    login_type = session.get('login_type', 'student')

    # Store user info in session
    session.permanent = True
    session["user"] = {
        "email": email,
        "displayName": user_data.get("displayName", email.split('@')[0]),
        "type": login_type
    }

    # Only validate email for student logins
    if login_type == 'student':
        if not email.endswith("@stu.upes.ac.in"):
            return "Access Denied: Please use your student email (@stu.upes.ac.in)", 403
        return redirect(url_for('home'))
    
    # For faculty login, set token and redirect to dashboard
    elif login_type == 'faculty':
        session['faculty_token'] = True
        return redirect(url_for('faculty_portal_dashboard'))

    return redirect(url_for('home'))

@app.route("/home")
def home():
    if "user" not in session:
        return redirect(url_for("login"))
    # Check if user is student before showing index page
    if session.get("user", {}).get("type") == "faculty":
        return redirect(url_for("faculty_portal_dashboard"))
    return render_template("index.html")

@app.route('/static/<path:filename>')
def serve_static(filename):
    try:
        app.logger.debug(f"Serving static file: {filename} from {app.static_folder}")
        return send_from_directory(app.static_folder, filename)
    except Exception as e:
        app.logger.error(f"Error serving static file {filename}: {str(e)}")
        app.logger.debug(f"Static folder contents: ['.DS_Store', 'styles.css', 'css', 'images', 'js', 'script.js', 'videos']")
        return "File not found", 404


@app.route('/caiindex', methods=['GET'])
def caiindex():
    return render_template('caiindex.html')

@app.route('/faculty_portal')
def faculty_portal():
    """Faculty portal entry point"""
    if 'faculty_token' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('faculty_portal_dashboard'))

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/faculty')
def faculty():
    """ProfConnect portal for students"""
    return render_template('faculty.html')

@app.route('/internship')
def internship():
    return render_template('internship.html')

@app.route('/api/services')
def get_services():
    return jsonify(knowledge_base.get('services', []))

@app.route('/api/faqs')
def get_faqs():
    return jsonify(knowledge_base.get('faqs', []))

@app.route('/api/announcements')
def get_announcements():
    try:
        announcements = knowledge_base.get('announcements', [])
        logger.info(f"Fetched {len(announcements)} regular announcements")
        return jsonify(announcements)
    except Exception as e:
        logger.exception("Error fetching regular announcements")
        return jsonify({"error": str(e)}), 500

@app.route('/announcements')
def announcements():
    return render_template('announcements.html')

from ai_model import query_deepseek  # Changed from query_mistral

@app.route('/api/query', methods=['POST'])
def query_api():
    data = request.get_json()
    prompt = data.get('prompt', '')
    
    if not prompt:
        return jsonify({'error': 'Prompt is required'}), 400
    
    # Function name remains the same but now uses Llama 3 internally
    response_text = query_deepseek(prompt)
    return jsonify({'response': response_text})

@app.route('/caichat')
def caichat():
    return render_template('caichat.html')

@app.route('/search')
def search():
    query = request.args.get('q', '').lower()
    results = []
    
    # Search through all sections
    for section, items in knowledge_base.items():
        for item in items:
            # Convert item to string for searching
            item_str = json.dumps(item).lower()
            if query in item_str:
                # Add section type to item
                item_with_type = item.copy()
                item_with_type['type'] = section
                results.append(item_with_type)
    
    return jsonify(results)

@app.route('/logout')
def logout():
    # Clear user session
    session.clear()
    # Redirect to Microsoft's logout endpoint
    # Get the logout URL from Azure AD configuration
    logout_url = (
        f"https://login.microsoftonline.com/{app.config['AZURE_OAUTH_TENANT']}/oauth2/v2.0/logout"
        f"?post_logout_redirect_uri=https://localhost:5001"
    )
    return redirect(logout_url)

@app.route('/lms')
def lms():
    return render_template('lms.html')

@app.route('/studentserv')
def student_services():
    return render_template('studentserv.html')

@app.route('/attendance')
def attendance():
    return render_template('attendance.html')

@app.route('/instaConnect')
def insta_connect():
    return render_template('instaConnect.html')

# InstaConnect API Endpoints
@app.route('/api/instaConnect/posts', methods=['POST'])
def create_insta_post():
    if not session.get("user"):
        return jsonify({'error': 'Unauthorized'}), 401
        
    data = request.get_json()
    content = data.get('content')
    
    if not content:
        return jsonify({'error': 'Content is required'}), 400
        
    # Create post logic here
    post = {
        'id': str(uuid.uuid4()),
        'content': content,
        'author': {
            'id': session['user'].get('id'),
            'name': session['user'].get('displayName'),
            'avatar': f"/static/images/{'male' if session['user'].get('gender') == 'male' else 'female'}.png"
        },
        'createdAt': datetime.now().isoformat()
    }
    
    return jsonify({'success': True, 'post': post}), 201

@app.route('/api/instaConnect/search', methods=['GET'])
def insta_search():
    if not session.get("user"):
        return jsonify({'error': 'Unauthorized'}), 401
        
    query = request.args.get('q', '')
    
    if len(query) < 3:
        return jsonify({'error': 'Query must be at least 3 characters'}), 400
        
    # Search logic here
    results = {
        'users': [],
        'projects': []
    }
    
    return jsonify(results)

def get_outlook_emails():
    """Fetch emails from Outlook using Microsoft Graph API"""
    if not azure_bp.session.authorized:
        return None
        
    # Get emails from the last 30 days
    start_date = (datetime.now() - timedelta(days=30)).isoformat()
    
    # Microsoft Graph API endpoint for messages
    endpoint = "https://graph.microsoft.com/v1.0/me/messages"
    
    # Query parameters to filter announcements
    params = {
        "$select": "subject,receivedDateTime,bodyPreview,from,importance",
        "$filter": f"receivedDateTime ge {start_date} and (subject contains 'Announcement' or subject contains 'Notice')",
        "$orderby": "receivedDateTime desc",
        "$top": 50  # Limit to 50 emails
    }
    
    try:
        response = azure_bp.session.get(endpoint, params=params)
        if response.ok:
            return response.json().get('value', [])
        return None
    except Exception as e:
        print(f"Error fetching emails: {e}")
        return None

@app.route('/api/outlook-announcements')
def get_outlook_announcements():
    """API endpoint to get Outlook announcements"""
    if "user" not in session:
        logger.warning("User not in session")
        return jsonify({"error": "Unauthorized"}), 401
        
    if not azure_bp.session.authorized:
        logger.warning("Azure session not authorized")
        return jsonify({"error": "Not authenticated with Outlook"}), 401

    try:
        # Microsoft Graph API endpoint for messages
        endpoint = "https://graph.microsoft.com/v1.0/me/mailFolders/inbox/messages"
        
        # Get emails from last 30 days
        thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
        
        # Query parameters
        params = {
            "$select": "id,subject,bodyPreview,receivedDateTime,from,importance",
            "$filter": f"receivedDateTime ge {thirty_days_ago}",
            "$orderby": "receivedDateTime desc",
            "$top": 50
        }
        
        logger.debug(f"Making request to Graph API: {endpoint}")
        response = azure_bp.session.get(endpoint, params=params)
        
        if not response.ok:
            logger.error(f"Graph API error: {response.status_code} - {response.text}")
            return jsonify({"error": "Failed to fetch emails"}), response.status_code
            
        emails = response.json().get('value', [])
        logger.info(f"Successfully fetched {len(emails)} emails")
        
        announcements = [{
            "id": email.get("id"),
            "title": email.get("subject", "No Subject"),
            "content": email.get("bodyPreview", ""),
            "date": email.get("receivedDateTime"),
            "from": email.get("from", {}).get("emailAddress", {}).get("name", "Unknown Sender"),
            "importance": email.get("importance", "normal"),
            "category": "Email Announcement",
            "isEmail": True
        } for email in emails if email.get("subject")]

        return jsonify(announcements)
        
    except Exception as e:
        logger.exception("Error fetching Outlook emails")
        return jsonify({"error": str(e)}), 500

@app.after_request
def add_ngrok_header(response):
    response.headers["ngrok-skip-browser-warning"] = "true"
    return response

# Faculty frontend routes with auth check
@app.route('/faculty_portal/dashboard')
def faculty_portal_dashboard():
    if 'faculty_token' not in session:
        return redirect(url_for('root'))
    return render_template('faculty_portal/dashboard.html')

@app.route('/faculty_portal/profconnect')
def faculty_portal_profconnect():
    if 'faculty_token' not in session:
        return redirect(url_for('faculty_portal'))
    return render_template('faculty_portal/profconnect.html')

@app.route('/faculty_portal/attendance')
def faculty_portal_attendance():
    return render_template('faculty_portal/attendance.html')

@app.route('/faculty_portal/lms')
def faculty_portal_lms():
    return render_template('faculty_portal/lms.html')

@app.route('/faculty_portal/timetable')
def faculty_portal_timetable():
    return render_template('faculty_portal/timetable.html')

@app.route('/faculty_portal/notifications')
def faculty_portal_notifications():
    return render_template('faculty_portal/notifications.html')

@app.route('/faculty_portal/courses')
def faculty_portal_courses():
    """Faculty courses portal"""
    if 'faculty_token' not in session:
        return redirect(url_for('root'))
    return render_template('faculty_portal/courses.html')

if __name__ == "__main__":
    from check_ollama import check_ollama_ready
    
    if not check_ollama_ready():
        logger.error("Ollama is not ready. Please ensure Ollama is installed and running with Llama 3.")
        sys.exit(1)
        
    app.run(debug=True, port=5001)
