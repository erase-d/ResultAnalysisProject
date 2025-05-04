from flask import Flask, render_template, request, jsonify, redirect, url_for
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_cors import CORS
from dotenv import load_dotenv
import os
import pandas as pd
import json
from datetime import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Import models
from models import db, User

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)
LOOKER_BASE_URL = "https://lookerstudio.google.com/reporting/c18e2663-f49b-4d0c-b52e-f9f751af31dc/page/grvIF"

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'secret')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///college.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Google Sheets setup
def get_google_sheet():
    scope = ['https://spreadsheets.google.com/feeds',
             'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    client = gspread.authorize(creds)
    return client.open('ResultAnalysisProject').worksheet('Course Results')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        try:
            logger.debug("Received login request")
            if request.is_json:
                data = request.get_json()
            else:
                data = request.form
                
            logger.debug(f"Login attempt for username: {data.get('username')}")
            
            user = User.query.filter_by(username=data['username']).first()
            if user and user.check_password(data['password']):
                login_user(user)
                logger.debug("Login successful")
                if request.is_json:
                    return jsonify({'message': 'Login successful', 'redirect': url_for('dashboard')})
                return redirect(url_for('dashboard'))
            else:
                logger.debug("Login failed - invalid credentials")
                if request.is_json:
                    return jsonify({'message': 'Invalid username or password'}), 401
                return render_template('login.html', error='Invalid username or password')
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            if request.is_json:
                return jsonify({'message': f'Login error: {str(e)}'}), 500
            return render_template('login.html', error='An error occurred during login')
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    if request.method == 'POST':
        batch = request.form.get('batch_year')
        semester = request.form.get('semester')
        course = request.form.get('course')

        looker_url = f"{LOOKER_BASE_URL}?Batch_year_={batch}&Semester_={semester}&Course_={course}"
        return render_template('dashboard.html', looker_url=looker_url)

    # Default case (GET): show empty iframe
    return render_template('dashboard.html', looker_url=None)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/upload', methods=['POST', 'GET'])
@login_required
def upload_data():
    if not current_user.is_admin:
        return jsonify({'message': 'Unauthorized'}), 403
        
    if 'file' not in request.files:
        return jsonify({'message': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No file selected'}), 400
    
    if file and file.filename.endswith('.csv'):
        try:
            # Read CSV file
            df = pd.read_csv(file)
            
            # Validate required columns
            required_columns = ['batch_year', 'semester', 'course_name', 'usn', 'grade']
            if not all(col in df.columns for col in required_columns):
                return jsonify({'message': 'CSV file must contain all required columns: batch_year, semester, course_name, usn, grade'}), 400
            
            # Get Google Sheet
            sheet = get_google_sheet()
            
            # Get existing data to check for duplicates
            existing_data = sheet.get_all_records()
            existing_df = pd.DataFrame(existing_data)
            
            # Filter out duplicates based on usn, course_name, batch_year, and semester
            if not existing_df.empty:
                df = df[~df.apply(lambda row: 
                    (row['usn'], row['course_name'], row['batch_year'], row['semester']) in 
                    zip(existing_df['usn'], existing_df['course_name'], 
                        existing_df['batch_year'], existing_df['semester']), axis=1)]
            
            if df.empty:
                return jsonify({'message': 'No new data to add. All records already exist.'}), 200
            
            # Convert new data to list of lists
            new_data = df.values.tolist()
            
            # Find the next empty row
            next_row = len(existing_data) + 2  # +2 because of header row and 1-based indexing
            
            # Append new data
            sheet.update(f'A{next_row}', new_data)
            
            return jsonify({
                'message': f'Successfully added {len(new_data)} new records to Google Sheets',
                'records_added': len(new_data)
            })
            
        except Exception as e:
            return jsonify({'message': f'Error processing file: {str(e)}'}), 400
    
    return jsonify({'message': 'Invalid file format. Please upload a CSV file'}), 400

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 