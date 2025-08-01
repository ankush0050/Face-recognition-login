from flask import Flask, request, jsonify, render_template, redirect, url_for, session
from flask_cors import CORS
import cv2
import numpy as np
import base64
import os
import json
from datetime import datetime
import logging

# Import our custom modules
from models.database import DatabaseManager
from models.face_recognition import FaceRecognitionSystem, FaceRecognitionUtils
from config import config

# Get absolute paths for templates and static files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'frontend', 'templates'))
STATIC_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'frontend', 'static'))

# Initialize Flask app with absolute paths
app = Flask(__name__, 
           template_folder=TEMPLATE_DIR,
           static_folder=STATIC_DIR)

# ============= SOLUTION 2: CACHE CLEARING CONFIGURATION =============
# Force template auto-reload and cache clearing
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Enable Jinja auto-reload for development
app.jinja_env.auto_reload = True
app.jinja_env.cache = {}

# Additional cache busting for development
if True:  # Always enable for this fix
    app.config['TEMPLATES_AUTO_RELOAD'] = True
    app.config['EXPLAIN_TEMPLATE_LOADING'] = True
    
# Clear any existing template cache
app.jinja_env.cache.clear()

print("✅ Template cache clearing enabled")
print("✅ Auto-reload configured for templates")
# ================================================================

# Debug: Print template and static folder paths
print(f"✅ Template folder: {app.template_folder}")
print(f"✅ Static folder: {app.static_folder}")

# Verify dashboard template exists
dashboard_path = os.path.join(app.template_folder, 'dashboard.html')
print(f"✅ Dashboard template exists: {os.path.exists(dashboard_path)}")

# Additional template verification
template_files = ['index.html', 'login.html', 'register.html', 'dashboard.html', 'admin.html']
for template in template_files:
    template_path = os.path.join(app.template_folder, template)
    exists = os.path.exists(template_path)
    print(f"✅ {template}: {'Found' if exists else 'Missing'}")

# Load configuration
env = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[env])

# Force development mode cache settings
app.config['TEMPLATES_AUTO_RELOAD'] = True
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

# Initialize CORS
CORS(app, resources={
    r"/api/*": {
        "origins": ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5000", "http://127.0.0.1:5000"],
        "methods": ["GET", "POST", "PUT", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Initialize our systems
db_manager = DatabaseManager()
face_system = FaceRecognitionSystem(tolerance=app.config.get('FACE_RECOGNITION_TOLERANCE', 0.6))

# Load existing face encodings on startup
def load_known_faces():
    """Load all known faces from database"""
    try:
        encodings, employee_ids = db_manager.get_all_face_encodings()
        face_system.load_known_faces(encodings, employee_ids)
        print(f"✅ Loaded {len(encodings)} known faces on startup")
    except Exception as e:
        print(f"⚠️ Error loading known faces: {e}")

# Initialize known faces
load_known_faces()

# Configure logging
if not app.debug:
    logging.basicConfig(level=logging.INFO)

# ============= ROUTES =============
@app.route('/static-test')
def static_test():
    css_path = os.path.join(app.static_folder, 'css', 'style.css')
    js_path = os.path.join(app.static_folder, 'js', 'face_capture.js')
    css_exists = os.path.exists(css_path)
    js_exists = os.path.exists(js_path)
    return f"""
    <h1>Static Files Test</h1>
    <p>CSS path: <b>{css_path}</b> → Exists: <b style='color:{'green' if css_exists else 'red'}'>{css_exists}</b></p>
    <p>JS path: <b>{js_path}</b> → Exists: <b style='color:{'green' if js_exists else 'red'}'>{js_exists}</b></p>
    <link rel="stylesheet" href="{{{{ url_for('static', filename='css/style.css') }}}}">
    <p style='color: green;'>If this text is green, CSS loaded correctly.</p>
    """

# ======= rest of your app/routes as before =======

@app.route('/')
def index():
    """Landing page"""
    try:
        # Clear template cache before rendering
        app.jinja_env.cache.clear()
        return render_template('index.html')
    except Exception as e:
        print(f"❌ Error rendering index.html: {e}")
        return f"Template error: {str(e)}", 500

@app.route('/login')
def login_page():
    """Face recognition login page"""
    try:
        # Clear template cache before rendering
        app.jinja_env.cache.clear()
        return render_template('login.html')
    except Exception as e:
        print(f"❌ Error rendering login.html: {e}")
        return f"Template error: {str(e)}", 500

@app.route('/register')
def register_page():
    """Employee registration page"""
    try:
        # Clear template cache before rendering
        app.jinja_env.cache.clear()
        return render_template('register.html')
    except Exception as e:
        print(f"❌ Error rendering register.html: {e}")
        return f"Template error: {str(e)}", 500

@app.route('/dashboard')
def dashboard():
    """Employee dashboard (after successful login)"""
    try:
        # Clear template cache before rendering
        app.jinja_env.cache.clear()
        
        employee_id = request.args.get('employee_id')
        if not employee_id:
            print(f"⚠️ No employee_id provided, redirecting to login")
            return redirect(url_for('login_page'))
        
        # Get employee details
        employee = db_manager.get_employee_by_id(employee_id)
        if not employee:
            print(f"⚠️ Employee {employee_id} not found, redirecting to login")
            return redirect(url_for('login_page'))
        
        # Get recent login history
        login_history = db_manager.get_login_history(employee_id, limit=10)
        
        # Verify template exists before rendering
        dashboard_template = os.path.join(app.template_folder, 'dashboard.html')
        if not os.path.exists(dashboard_template):
            print(f"❌ Dashboard template not found at: {dashboard_template}")
            return f"Dashboard template missing at: {dashboard_template}", 500
        
        print(f"✅ Rendering dashboard for employee: {employee['name']}")
        print(f"✅ Using template: {dashboard_template}")
        
        return render_template('dashboard.html', 
                             employee=employee, 
                             login_history=login_history)
    except Exception as e:
        print(f"❌ Error in dashboard route: {e}")
        import traceback
        traceback.print_exc()
        return f"Dashboard error: {str(e)}", 500

@app.route('/admin')
def admin_panel():
    """Admin panel for managing employees"""
    try:
        # Clear template cache before rendering
        app.jinja_env.cache.clear()
        
        employees = db_manager.get_all_employees()
        stats = db_manager.get_stats()
        recent_logins = db_manager.get_login_history(limit=20)
        
        return render_template('admin.html',
                             employees=employees,
                             stats=stats,
                             recent_logins=recent_logins)
    except Exception as e:
        print(f"❌ Error rendering admin.html: {e}")
        return f"Template error: {str(e)}", 500

# ============= API ENDPOINTS =============

@app.route('/api/recognize', methods=['POST'])
def api_recognize_face():
    """API endpoint for face recognition login"""
    try:
        data = request.get_json()
        
        if not data or 'image' not in data:
            return jsonify({
                'success': False,
                'message': 'No image data provided'
            }), 400
        
        # Process the image
        image = face_system.process_image_from_base64(data['image'])
        
        if image is None:
            return jsonify({
                'success': False,
                'message': 'Invalid image format'
            }), 400
        
        # Validate face quality
        is_valid, quality_message = face_system.validate_face_quality(image)
        
        if not is_valid:
            # Log failed attempt
            db_manager.log_login_attempt(
                employee_id=None,
                confidence=0.0,
                success=False,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                failure_reason=quality_message
            )
            
            return jsonify({
                'success': False,
                'message': quality_message
            }), 400
        
        # Attempt face recognition
        employee_id, confidence = face_system.recognize_face(image)
        
        min_confidence = app.config.get('MIN_CONFIDENCE_THRESHOLD', 0.7)
        if employee_id and confidence > min_confidence:
            # Get employee details
            employee = db_manager.get_employee_by_id(employee_id)
            
            if employee and employee['is_active']:
                # Log successful login
                db_manager.log_login_attempt(
                    employee_id=employee_id,
                    confidence=confidence,
                    success=True,
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent')
                )
                
                return jsonify({
                    'success': True,
                    'employee_id': employee_id,
                    'employee_name': employee['name'],
                    'confidence': float(confidence),
                    'message': f'Welcome back, {employee["name"]}! Confidence: {confidence:.1%}',
                    'redirect_url': f'/dashboard?employee_id={employee_id}'
                })
            else:
                failure_reason = 'Employee account inactive'
        else:
            failure_reason = f'Face not recognized (confidence: {confidence:.1%})'
        
        # Log failed attempt
        db_manager.log_login_attempt(
            employee_id=employee_id if confidence and confidence > 0.3 else None,
            confidence=confidence or 0.0,
            success=False,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            failure_reason=failure_reason
        )
        
        return jsonify({
            'success': False,
            'message': 'Face not recognized or confidence too low. Please try again.',
            'confidence': float(confidence) if confidence else 0.0
        })
        
    except Exception as e:
        app.logger.error(f"Error in face recognition: {str(e)}")
        print(f"❌ Face recognition error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error during face recognition'
        }), 500

@app.route('/api/register', methods=['POST'])
def api_register_employee():
    """API endpoint for employee registration"""
    try:
        data = request.get_json()
        
        required_fields = ['employee_id', 'name', 'email', 'department', 'image']
        for field in required_fields:
            if field not in data or not data[field]:
                return jsonify({
                    'success': False,
                    'message': f'Missing required field: {field}'
                }), 400
        
        # Process the image
        image = face_system.process_image_from_base64(data['image'])
        
        if image is None:
            return jsonify({
                'success': False,
                'message': 'Invalid image format'
            }), 400
        
        # Validate face quality
        is_valid, quality_message = face_system.validate_face_quality(image)
        
        if not is_valid:
            return jsonify({
                'success': False,
                'message': quality_message
            }), 400
        
        # Generate face encoding
        face_encoding = face_system.encode_face(image)
        
        if face_encoding is None:
            return jsonify({
                'success': False,
                'message': 'Could not generate face encoding. Please try with a clearer image.'
            }), 400
        
        # Save employee to database
        success = db_manager.add_employee(
            employee_id=data['employee_id'],
            name=data['name'],
            email=data['email'],
            department=data['department'],
            face_encoding=face_encoding
        )
        
        if success:
            # Reload known faces to include the new employee
            load_known_faces()
            
            return jsonify({
                'success': True,
                'message': f'Employee {data["name"]} registered successfully!',
                'employee_id': data['employee_id']
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to register employee. Employee ID or email might already exist.'
            }), 400
            
    except Exception as e:
        app.logger.error(f"Error in employee registration: {str(e)}")
        print(f"❌ Registration error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Internal server error during registration'
        }), 500

@app.route('/api/employees', methods=['GET'])
def api_get_employees():
    """Get all employees"""
    try:
        employees = db_manager.get_all_employees()
        return jsonify({
            'success': True,
            'employees': employees
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/employees/<employee_id>', methods=['GET'])
def api_get_employee(employee_id):
    """Get specific employee details"""
    try:
        employee = db_manager.get_employee_by_id(employee_id)
        if employee:
            return jsonify({
                'success': True,
                'employee': employee
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Employee not found'
            }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/employees/<employee_id>', methods=['PUT'])
def api_update_employee(employee_id):
    """Update employee information"""
    try:
        data = request.get_json()
        success = db_manager.update_employee(employee_id, **data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Employee updated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to update employee'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/employees/<employee_id>', methods=['DELETE'])
def api_delete_employee(employee_id):
    """Delete (deactivate) employee"""
    try:
        success = db_manager.delete_employee(employee_id)
        
        if success:
            # Reload known faces after deletion
            load_known_faces()
            
            return jsonify({
                'success': True,
                'message': 'Employee deactivated successfully'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to deactivate employee'
            }), 400
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/login-history', methods=['GET'])
def api_get_login_history():
    """Get login history"""
    try:
        employee_id = request.args.get('employee_id')
        limit = int(request.args.get('limit', 50))
        
        history = db_manager.get_login_history(employee_id, limit)
        
        return jsonify({
            'success': True,
            'login_history': history
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/stats', methods=['GET'])
def api_get_stats():
    """Get system statistics"""
    try:
        stats = db_manager.get_stats()
        return jsonify({
            'success': True,
            'stats': stats
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

@app.route('/api/search', methods=['GET'])
def api_search_employees():
    """Search employees"""
    try:
        query = request.args.get('q', '')
        if not query:
            return jsonify({
                'success': False,
                'message': 'Search query required'
            }), 400
        
        results = db_manager.search_employees(query)
        return jsonify({
            'success': True,
            'results': results
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500

# ============= ERROR HANDLERS =============

@app.errorhandler(404)
def not_found(error):
    try:
        app.jinja_env.cache.clear()
        return render_template('404.html'), 404
    except:
        return "404 - Page Not Found", 404

@app.errorhandler(500)
def internal_error(error):
    try:
        app.jinja_env.cache.clear()
        return render_template('500.html'), 500
    except:
        return "500 - Internal Server Error", 500

# ============= STARTUP =============

def create_directories():
    """Create necessary directories on startup"""
    directories = [
        app.config.get('UPLOAD_FOLDER', 'backend/data/employee_photos'),
        app.config.get('TEMP_FOLDER', 'backend/data/temp'),
        'logs'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Directory created/verified: {directory}")

if __name__ == '__main__':
    try:
        # Create necessary directories
        create_directories()
        
        # Initialize database
        db_manager.init_database()
        
        # Load known faces
        load_known_faces()
        
        print("🚀 Face Recognition Employee Login System starting...")
        print(f"📊 Loaded {len(face_system.known_encodings)} known face encodings")
        print(f"🌐 Server running at: http://localhost:5000")
        print(f"🔗 Access your application at: http://127.0.0.1:5000")
        
        # Final cache clear before starting
        app.jinja_env.cache.clear()
        print("✅ Template cache cleared before startup")
        
        # Run the Flask application
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=True,
            threaded=True
        )
        
    except Exception as e:
        print(f"❌ Error starting Flask application: {e}")
        print("Please check your configuration and try again.")
