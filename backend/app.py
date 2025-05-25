


from flask import Flask, send_from_directory
from flask_cors import CORS
from routes.userRoutes import auth
from config.db import connect_db
from dotenv import load_dotenv
import os

app = Flask(__name__)

# Load environment variables from .env
load_dotenv()

# Ensure uploads folder exists
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Connect to the database
connect_db()

# Serve files from the uploads folder
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

# Basic hello route
@app.route('/')
def hello():
    return "Hello"

# Enable CORS for frontend (like Express setup)
CORS(app,
     origins=['http://localhost:5173'],
     supports_credentials=True,
     methods=['GET', 'POST', 'PUT', 'DELETE'],
     allow_headers=['Content-Type', 'Authorization']
)

# Register user-related routes
app.register_blueprint(auth, url_prefix='/api/users')

# Run the server
if __name__ == '__main__':
    PORT = int(os.getenv('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT)
