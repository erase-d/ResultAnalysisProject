# College Department Data Visualization System

This web application allows authorized users to visualize and analyze student performance data across different batches and semesters using LookerStudio integration.

## Features
- User authentication system
- Batch and semester selection
- Course-wise performance visualization
- NLP-based performance summarization
- Interactive charts and graphs

## Setup Instructions

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
Create a `.env` file with the following variables:
```
SECRET_KEY=your_secret_key
POWERBI_CLIENT_ID=your_powerbi_client_id
POWERBI_CLIENT_SECRET=your_powerbi_client_secret
POWERBI_TENANT_ID=your_powerbi_tenant_id
```

3. Initialize the database:
```bash
python init_db.py
```

4. Run the application:
```bash
python app.py
```

5. Access the application at `http://localhost:5000`

## Project Structure
- `app.py`: Main Flask application
- `models.py`: Database models
- `routes.py`: API routes
- `utils.py`: Utility functions
- `templates/`: HTML templates
- `static/`: Static files (CSS, JS)
- `data/`: Data storage directory 
