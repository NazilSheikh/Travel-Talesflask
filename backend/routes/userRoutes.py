

from flask import Blueprint, request, jsonify
from models.User import User
from models.travelStoryModel import Travelstory
import bcrypt
import jwt
import os
from functools import wraps
from datetime import datetime

auth = Blueprint('auth', __name__)

# ------------------------ AUTH HELPERS ------------------------

def serialize_mongo(obj):
    doc = obj.to_mongo().to_dict()
    doc['_id'] = str(doc['_id'])
    if 'userid' in doc:
        doc['userid'] = str(doc['userid'])
    return doc

def is_logged_in(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.cookies.get('token') or (
            request.headers.get('Authorization').split(" ")[1] if request.headers.get('Authorization') else None
        )
        if not token:
            return jsonify({"error": "Unauthorized: No token provided"}), 401
        try:
            data = jwt.decode(token, os.getenv("JWT_SECRET"), algorithms=["HS256"])
            request.user = data
            return f(*args, **kwargs)
        except Exception as e:
            print("JWT Error:", e)
            return jsonify({"error": "Unauthorized: Invalid token"}), 401
    return decorated_function

# ------------------------ AUTH ROUTES ------------------------

@auth.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        password = data.get('password')

        if not name or not email or not password:
            return jsonify({"error": "All fields are required"}), 400

        if User.objects(email=email).first():
            return jsonify({"error": "User already registered"}), 400

        salt = bcrypt.gensalt()
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)

        User(
            name=name,
            email=email,
            password=hashed_password.decode('utf-8')
        ).save()

        token = jwt.encode(
            {"email": email},
            os.getenv("JWT_SECRET"),
            algorithm="HS256"
        )

        response = jsonify({"message": "Registered Successfully"})
        response.set_cookie("token", token, httponly=True)
        return response, 201

    except Exception as e:
        print("Server Error:", e)
        return jsonify({"error": "Server Error"}), 500


@auth.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')

        user = User.objects(email=email).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        if bcrypt.checkpw(password.encode('utf-8'), user.password.encode('utf-8')):
            token = jwt.encode(
                {"email": user.email, "userid": str(user.id)},
                os.getenv("JWT_SECRET"),
                algorithm="HS256"
            )

            response = jsonify({"message": "Logged in Successfully", "token": token})
            response.set_cookie("token", token, httponly=True)
            return response, 200
        else:
            return jsonify({"error": "Invalid credentials"}), 401

    except Exception as e:
        print("Login Error:", e)
        return jsonify({"error": "Server Error"}), 500


@auth.route('/get-user', methods=['GET'])
@is_logged_in
def get_user():
    try:
        user = User.objects(email=request.user['email']).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        user_dict = {
            "id": str(user.id),
            "name": user.name,
            "email": user.email,
        }
        return jsonify(user_dict), 200
    except Exception as e:
        print("Get User Error:", e)
        return jsonify({"error": "Server Error"}), 500


# ------------------------ TRAVEL STORY ROUTES ------------------------

@auth.route('/allrequired', methods=['POST'])
@is_logged_in
def add_travel_story():
    try:
        data = request.get_json()
        title = data.get('title')
        story = data.get('story')
        visitedLocation = data.get('visitedLocation')
        imageUrl = data.get('imageUrl')
        visitedDate_ms = data.get('visitedDate')  # expecting milliseconds timestamp

        userid = request.user.get('userid')
        email = request.user.get('email')

        if not all([title, story, visitedLocation, imageUrl, visitedDate_ms]):
            return jsonify({"error": True, "message": "All fields are required"}), 400

        user = User.objects(id=userid).only('name').first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        visitedDate = datetime.utcfromtimestamp(int(visitedDate_ms) / 1000)

        travel_story = Travelstory(
            title=title,
            story=story,
            visitedLocation=visitedLocation,
            imageUrl=imageUrl,
            visitedDate=visitedDate,
            userid=userid,
            name=user.name,
            email=email
        )
        travel_story.save()

        return jsonify({"story": serialize_mongo(travel_story), "message": "Added Successfully"}), 201

    except Exception as e:
        return jsonify({"error": True, "message": str(e)}), 400


@auth.route('/getalltravelstory', methods=['GET'])
@is_logged_in
def get_all_travel_stories():
    try:
        userid = request.user.get('userid')

        stories = Travelstory.objects(userid=userid).order_by('-isFavorite')
        stories_list = [serialize_mongo(story) for story in stories]

        return jsonify({"story": stories_list}), 200

    except Exception as e:
        return jsonify({"error": True, "message": str(e)}), 400




@auth.route('/getpublicstories', methods=['GET'])
def get_public_stories():
    try:
        stories = Travelstory.objects().only(
            'title', 'story', 'visitedLocation', 'imageUrl',
            'visitedDate', 'name', 'email', 'userid',
            'createdOn', 'isFavorite'
        ).order_by('-createdAt')  # Sort by newest first

        stories_list = [serialize_mongo(story) for story in stories]

        return jsonify({ "stories": stories_list }), 200
    except Exception as error:
        return jsonify({ "error": True, "message": str(error) }), 400
    

    
from flask import request, jsonify
import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')  # Example path
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@auth.route('/upload-image', methods=['POST'])
def upload_image():
    if 'image' not in request.files:
        return jsonify({'error': 'No image part'}), 400

    file = request.files['image']

    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        return jsonify({'message': 'Image uploaded successfully', 'imageUrl': f'/uploads/{filename}'}), 201
    else:
        return jsonify({'error': 'Invalid file type'}), 400

@auth.route('/delete-image/<filename>', methods=['DELETE'])
def delete_image(filename):
    if not allowed_file(filename):
        return jsonify({'error': 'Invalid file type'}), 400

    file_path = os.path.join(UPLOAD_FOLDER, filename)

    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            return jsonify({'message': 'Image deleted successfully'}), 200
        except Exception as e:
            return jsonify({'error': f'Error deleting file: {str(e)}'}), 500
    else:
        return jsonify({'error': 'File not found'}), 404
    
@auth.route('/edit-story/<string:id>', methods=['PUT'])
@is_logged_in
def edit_story(id):
    data = request.get_json()

    title = data.get('title')
    story = data.get('story')
    visitedLocation = data.get('visitedLocation')
    imageUrl = data.get('imageUrl')
    visitedDate_ms = data.get('visitedDate')
    userid = request.user.get('userid')  # Assumes JWT middleware adds this

    if not all([title, story, visitedLocation, visitedDate_ms]):
        return jsonify({"error": True, "message": "All fields are required"}), 400

    try:
        # Convert ms to datetime
        parsedVisitedDate = datetime.utcfromtimestamp(int(visitedDate_ms) / 1000)

        # Validate ObjectId if needed
        try:
            travel_story = Travelstory.objects.get(id=id, userid=userid)
        except (DoesNotExist, ValidationError):
            return jsonify({"error": True, "message": "Story not found"}), 404

        # Set default image if not provided
        placeholderUrl = "http://localhost:3000/assets/pexels-stywo-1261728.jpg"

        # Update fields
        travel_story.update(
            title=title,
            story=story,
            visitedLocation=visitedLocation,
            imageUrl=imageUrl or placeholderUrl,
            visitedDate=parsedVisitedDate
        )

        return jsonify({"error": False, "message": "Updated successfully"}), 200

    except Exception as e:
        return jsonify({"error": True, "message": str(e)}), 500

@auth.route('/delete/<id>', methods=['DELETE'])
@is_logged_in
def delete_story(id):
    userid = request.user.get('userid')

    try:
        travel_story = Travelstory.objects(id=id, userid=userid).first()
        if not travel_story:
            return jsonify({"error": True, "message": "Travel story not found"}), 404

        imageUrl = travel_story.imageUrl
        # Delete DB record first
        Travelstory.objects(id=id, userid=userid).delete()

        # Delete image file from uploads folder
        filename = os.path.basename(imageUrl)
        filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'uploads', filename)

        try:
            if os.path.exists(filepath):
                os.remove(filepath)
        except Exception as e:
            print(f"Failed to delete image file: {e}")

        return jsonify({"message": "Data deleted successfully"}), 200

    except Exception as e:
        return jsonify({"error": True, "message": str(e)}), 500


@auth.route('/search', methods=['GET'])
def search_stories():
    query = request.args.get('query')

    if not query:
        return jsonify({"message": "No travel story found"}), 401

    try:
        search_result = Travelstory.objects(
            __raw__={
                "$or": [
                    {"title": {"$regex": query, "$options": "i"}},
                    {"story": {"$regex": query, "$options": "i"}},
                    {"visitedLocation": {"$regex": query, "$options": "i"}}
                ]
            }
        ).order_by('-isFavorite')

        return jsonify({"story": [story.to_json() for story in search_result]}), 200
    except Exception as e:
        return jsonify({"error": True, "message": str(e)}), 500
    
     

@auth.route('/filterbydate', methods=['GET'])
def filter_by_date():
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')

    if not start_date or not end_date:
        return jsonify({"message": "Start and end dates are required"}), 400

    try:
        start = datetime.fromtimestamp(int(start_date) / 1000)
        end = datetime.fromtimestamp(int(end_date) / 1000)

        stories = Travelstory.objects(
            visitedDate__gte=start,
            visitedDate__lte=end
        ).order_by('-isFavorite')

        return jsonify({"story": [story.to_json() for story in stories]}), 200
    except Exception as e:
        return jsonify({"error": True, "message": str(e)}), 500
