from flask import Flask, render_template, request, jsonify
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from flask_cors import CORS
from dotenv import load_dotenv
import os
import pandas as pd
from transformers import pipeline
from powerbiclient import Report, models
import json

# Import models
from models import db, User, CourseData

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Configuration
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///college.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    user = User.query.filter_by(username=data['username']).first()
    if user and user.check_password(data['password']):
        login_user(user)
        return jsonify({'message': 'Login successful'})
    return jsonify({'message': 'Invalid credentials'}), 401

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return jsonify({'message': 'Logged out successfully'})

@app.route('/api/batches')
@login_required
def get_batches():
    batches = CourseData.query.with_entities(CourseData.batch_year).distinct().all()
    return jsonify([batch[0] for batch in batches])

@app.route('/api/semesters/<batch>')
@login_required
def get_semesters(batch):
    semesters = CourseData.query.filter_by(batch_year=batch).with_entities(CourseData.semester).distinct().all()
    return jsonify([sem[0] for sem in semesters])

@app.route('/api/courses/<batch>/<semester>')
@login_required
def get_courses(batch, semester):
    courses = CourseData.query.filter_by(batch_year=batch, semester=semester).with_entities(CourseData.course_name).distinct().all()
    return jsonify([course[0] for course in courses])

@app.route('/api/visualization/<batch>/<semester>/<course>')
@login_required
def get_visualization(batch, semester, course):
    # Get data for the selected course
    data = CourseData.query.filter_by(
        batch_year=batch,
        semester=semester,
        course_name=course
    ).all()
    
    # Convert to DataFrame for analysis
    df = pd.DataFrame([{
        'roll_no': d.roll_no,
        'student_name': d.student_name,
        'grade': d.grade
    } for d in data])
    
    # Generate grade distribution
    grade_dist = df['grade'].value_counts().to_dict()
    
    # Generate PowerBI report
    report = Report(
        workspace_id=os.getenv('POWERBI_WORKSPACE_ID'),
        report_id=os.getenv('POWERBI_REPORT_ID')
    )
    
    # Generate NLP summary
    summarizer = pipeline("summarization")
    summary = summarizer(
        f"Grade distribution for {course}: {json.dumps(grade_dist)}",
        max_length=130,
        min_length=30
    )[0]['summary_text']
    
    return jsonify({
        'grade_distribution': grade_dist,
        'powerbi_report': report.get_embed_token(),
        'summary': summary
    })

@app.route('/api/upload', methods=['POST'])
@login_required
def upload_data():
    if 'file' not in request.files:
        return jsonify({'message': 'No file uploaded'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'message': 'No file selected'}), 400
    
    if file and file.filename.endswith('.csv'):
        df = pd.read_csv(file)
        for _, row in df.iterrows():
            course_data = CourseData(
                roll_no=row['roll_no'],
                student_name=row['student_name'],
                grade=row['grade'],
                batch_year=row['batch_year'],
                semester=row['semester'],
                course_name=row['course_name']
            )
            db.session.add(course_data)
        db.session.commit()
        return jsonify({'message': 'Data uploaded successfully'})
    
    return jsonify({'message': 'Invalid file format'}), 400

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True) 