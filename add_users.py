from werkzeug.security import generate_password_hash
import sqlite3

# Connect to the database
conn = sqlite3.connect('ResultAnalysisProject/college.db')
cursor = conn.cursor()

# Dummy users data
users = [
    ('admin', 'admin123', True),  # Admin user
    ('teacher1', 'teacher123', False),  # Regular teacher
    ('teacher2', 'teacher456', False),  # Regular teacher
    ('hod', 'hod123', True)  # HOD with admin privileges
]

# Insert users with hashed passwords
for username, password, is_admin in users:
    password_hash = generate_password_hash(password)
    cursor.execute(
        'INSERT INTO user (username, password_hash, is_admin) VALUES (?, ?, ?)',
        (username, password_hash, is_admin)
    )

# Commit changes and close connection
conn.commit()
conn.close()

print("Dummy users added successfully!") 