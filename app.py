from flask import Flask, redirect, render_template, session , request, jsonify, send_file, send_from_directory, url_for
from flask_cors import CORS
from flask_mail import Mail, Message
from pymongo import MongoClient
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import os
from dotenv import load_dotenv
import logging
from werkzeug.utils import secure_filename

import os




ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif' , 'webp'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Set your secret key for session management
CORS(app)  # Enable CORS for all routes
CORS(app, resources={r"/*": {"origins": "*"}})


UPLOAD_FOLDER = os.path.join(app.static_folder, 'uploads')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Flask-Mail configuration for email sending
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('EMAIL_USER')
app.config['MAIL_PASSWORD'] = os.getenv('EMAIL_PASS')
app.config['MAIL_DEBUG'] = True

mail = Mail(app)

# MongoDB configuration
client = MongoClient(os.getenv('MONGODB_URI'))
db = client['RamDB']  # Database name
users_collection = db['users'] 

# Load the dataset and preprocess it
data = pd.read_csv("Districts.csv")
data['Sqft'] = data['Sqft'].str.replace(',', '').astype(float)  # Convert Sqft to float
data_encoded = pd.get_dummies(data, columns=['District'])

# Split the dataset into features (X) and target variable (y)
X = data_encoded.drop(columns=["Price", "Address", "Predicted Price"])
y = data_encoded["Price"]

# Train the Random Forest model
rf_model = RandomForestRegressor(n_estimators=700, max_depth=10, min_samples_split=5, min_samples_leaf=2, random_state=42)  
rf_model.fit(X, y)



# Set the path for the uploads folder inside static
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'uploads')

# Ensure the uploads folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])


@app.route('/')
def index():
    user_logged_in = 'username' in session  # Check if the user is logged in
    username = session.get('username')  # Get the username from the session
    looking_for = session.get('looking_for')  # Get the 'Looking For' data from the session
    return render_template('index.html', user_logged_in=user_logged_in, username=username, looking_for=looking_for)

@app.route('/logout')
def logout():
    session.pop('username', None)  # Remove user from session
    return redirect('/')


@app.route('/about.html')
def about():
    user_logged_in = 'username' in session  # Check if the user is logged in
    username = session.get('username')  # Get the username from the session
    looking_for = session.get('looking_for')  # Get the 'Looking For' data from the session
    return render_template('about.html', user_logged_in=user_logged_in, username=username, looking_for=looking_for)

@app.route('/property-grid.html')
def property():
    user_logged_in = 'username' in session  # Check if the user is logged in
    username = session.get('username')  # Get the username from the session
    looking_for = session.get('looking_for')  # Get the 'Looking For' data from the session
    return render_template('property-grid.html', user_logged_in=user_logged_in, username=username, looking_for=looking_for)

@app.route('/contact.html')
def contact():
    user_logged_in = 'username' in session  # Check if the user is logged in
    username = session.get('username')  # Get the username from the session
    looking_for = session.get('looking_for')  # Get the 'Looking For' data from the session
    return render_template('contact.html', user_logged_in=user_logged_in, username=username, looking_for=looking_for)

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect('/login')  # Redirect to login if user is not logged in

    username = session.get('username')
    looking_for = session.get('looking_for')
    
    # Retrieve user details from the database
    user = users_collection.find_one({"fullName": username})

    if user is None:
        return jsonify({"message": "User not found"}), 404
    
    print(f"Profile Picture: {user.get('profilePicture')}")

    # Pass the user's email and profile picture to the template
    return render_template('dashboard.html', 
                           username=username, 
                           user_email=user.get('email'), 
                           looking_for=looking_for, 
                           profile_picture=user.get('profilePicture'))



@app.route('/update-email', methods=['POST'])
def update_email():
    if 'username' not in session:
        return jsonify({"message": "Unauthorized"}), 401
    
    data = request.get_json()
    new_email = data.get("email")
    
    # Update the user's email in the database
    users_collection.update_one({"fullName": session['username']}, {"$set": {"email": new_email}})
    
    return jsonify({"message": "Email updated successfully"}), 200


@app.route('/update-password', methods=['POST'])
def update_password():
    if 'username' not in session:
        return jsonify({"message": "Unauthorized"}), 401
    
    data = request.get_json()
    new_password = data.get("password")
    
    # Update the user's password in the database
    users_collection.update_one({"fullName": session['username']}, {"$set": {"password": new_password}})
    
    return jsonify({"message": "Password updated successfully"}), 200


@app.route('/delete-account', methods=['DELETE'])
def delete_account():
    if 'username' not in session:
        return jsonify({"message": "Unauthorized"}), 401

    # Delete the user from the database
    users_collection.delete_one({"fullName": session['username']})

    # Clear the session
    session.clear()
    
    return jsonify({"message": "Account deleted successfully"}), 200

@app.route('/update-username', methods=['POST'])
def update_username():
    if 'username' not in session:
        return jsonify({"message": "Unauthorized"}), 401

    data = request.get_json()
    new_username = data.get("username")

    # Validate new_username
    if not new_username:
        return jsonify({"message": "New username is required"}), 400

    # Update the user's username in the database
    result = users_collection.update_one(
        {"fullName": session['username']},
        {"$set": {"fullName": new_username}}
    )

    if result.modified_count == 0:
        return jsonify({"message": "No changes made, username may be the same."}), 400

    # Update the session with the new username
    session['username'] = new_username

    return jsonify({"message": "Username updated successfully"}), 200



@app.route('/login.html')
def login():
    return render_template('login.html')

@app.route('/signup.html')
def signup():
    return render_template('signup.html')





@app.route('/property-single1.html')
def property_single1():
    user_logged_in = 'username' in session  # Check if the user is logged in
    username = session.get('username')  # Get the username from the session
    looking_for = session.get('looking_for')  # Get the 'Looking For' data from the session
    return render_template('property-single1.html', user_logged_in=user_logged_in, username=username, looking_for=looking_for)

@app.route('/property-single2.html')
def property_single2():
    user_logged_in = 'username' in session  # Check if the user is logged in
    username = session.get('username')  # Get the username from the session
    looking_for = session.get('looking_for')  # Get the 'Looking For' data from the session
    return render_template('property-single2.html', user_logged_in=user_logged_in, username=username, looking_for=looking_for)

@app.route('/property-single3.html')
def property_single3():
    user_logged_in = 'username' in session  # Check if the user is logged in
    username = session.get('username')  # Get the username from the session
    looking_for = session.get('looking_for')  # Get the 'Looking For' data from the session
    return render_template('property-single3.html', user_logged_in=user_logged_in, username=username, looking_for=looking_for)

@app.route('/property-single4.html')
def property_single4():
    user_logged_in = 'username' in session  # Check if the user is logged in
    username = session.get('username')  # Get the username from the session
    looking_for = session.get('looking_for')  # Get the 'Looking For' data from the session
    return render_template('property-single4.html', user_logged_in=user_logged_in, username=username, looking_for=looking_for)

@app.route('/property-single5.html')
def property_single5():
    user_logged_in = 'username' in session  # Check if the user is logged in
    username = session.get('username')  # Get the username from the session
    looking_for = session.get('looking_for')  # Get the 'Looking For' data from the session
    return render_template('property-single5.html', user_logged_in=user_logged_in, username=username, looking_for=looking_for)

@app.route('/property-single6.html')
def property_single6():
    user_logged_in = 'username' in session  # Check if the user is logged in
    username = session.get('username')  # Get the username from the session
    looking_for = session.get('looking_for')  # Get the 'Looking For' data from the session
    return render_template('property-single6.html', user_logged_in=user_logged_in, username=username, looking_for=looking_for)

@app.route('/property-single7.html')
def property_single7():
    user_logged_in = 'username' in session  # Check if the user is logged in
    username = session.get('username')  # Get the username from the session
    looking_for = session.get('looking_for')  # Get the 'Looking For' data from the session
    return render_template('property-single7.html', user_logged_in=user_logged_in, username=username, looking_for=looking_for)

@app.route('/test_css')
def test_css():
    return f'<link rel="stylesheet" href="{url_for("static", filename="assets/css/style.css")}">'

@app.route('/templates/nav.html')
def nav():
    return render_template('nav.html')

@app.route('/templates/footer.html')
def footer():
    return render_template('footer.html')


@app.route('/predict', methods=['POST'])
def predict():
    sqft = float(request.form['sqft'])
    district = request.form['district']

    # Prepare input data for prediction
    input_data = pd.DataFrame({
        'Sqft': [sqft],
        **{f'District_{district}': [1]}
    })
    for col in X.columns:
        if col not in input_data.columns:
            input_data[col] = 0
    input_data = input_data[X.columns]

    # Make prediction
    predicted_price = rf_model.predict(input_data)[0]

    # Return as plain text for the modal
    return f'Predicted Price: ₹{predicted_price:.2f}'

# Email sending endpoint
@app.route('/send', methods=['POST'])
def send_email():
    try:
        data = request.json
        print('Received data:', data)
        name = data.get('name')
        email = data.get('email')
        subject = data.get('subject')
        message = data.get('message')

        # Compose the email
        msg = Message(
            subject=f"New Contact Form Submission: {subject}",
            sender=app.config['MAIL_USERNAME'],
            recipients=['rentfindr@gmail.com']  # Your receiving email
        )
        msg.html = f"""
            <h3>New Contact Form Message</h3>
            <p><strong>Name:</strong> {name}</p>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>Subject:</strong> {subject}</p>
            <p><strong>Message:</strong></p>
            <p>{message}</p>
        """
        mail.send(msg)

        return jsonify({'message': 'Email sent successfully'})
    except Exception as e:
        print('Error sending email:', e)
        return jsonify({'message': 'Error sending email'}), 500
    
@app.route('/signup', methods=['POST'])
def signup_user():
    data = request.form  # Correctly accessing form data
    profile_picture = request.files.get("profilePicture")  # Get the uploaded file
    logging.debug("Received data: %s", data)

    # Retrieve each value from the data
    full_name = data.get("fullName")
    email = data.get("email")
    password = data.get("password")
    confirm_password = data.get("confirmPassword")
    looking_for = data.get("lookingFor")  # Collect looking for option
    profile_picture = request.files.get("profilePicture")

    logging.debug(f"Full Name: {full_name}, Email: {email}, Looking For: {looking_for}, Profile Picture: {profile_picture}")

    # Additional checks
    if not email:
        return jsonify({"message": "Email is required"}), 400

    if password != confirm_password:
        return jsonify({"message": "Passwords do not match"}), 400

    if profile_picture and allowed_file(profile_picture.filename):
        filename = secure_filename(profile_picture.filename)
        profile_picture.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    else:
        filename = None  # Handle the case when the profile picture is not provided

    try:
        # Insert new user data into the 'users' collection
        users_collection = db["users"]

        # Check if email already exists
        existing_user = users_collection.find_one({"email": email})
        if existing_user:
            return jsonify({"message": "Email already registered"}), 400

        new_user = {
            "fullName": full_name,
            "email": email,
            "password": password,
            "lookingFor": looking_for,
            "profilePicture": filename  # Store filename or path in your database
        }

        logging.debug(f"New User: {new_user}")  # Log the new user details
        users_collection.insert_one(new_user)

        # Save the user's info in the session
        session['username'] = full_name
        session['looking_for'] = looking_for

        return jsonify({"message": "User registered successfully"}), 201
    except Exception as error:
        logging.error("Error registering user: %s", error)
        return jsonify({"message": "Error registering user"}), 500




# Login route
@app.route('/login', methods=['POST'])
def login_user():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    try:
        users_collection = db["users"]
        user = users_collection.find_one({"email": email})

        if not user:
            return jsonify({"message": "User not found"}), 404

        if user["password"] != password:
            return jsonify({"message": "Incorrect password"}), 401

        # Set session after successful login
        session['username'] = user.get('fullName')  # or user.get('email'), depending on your preference

        # Send a success response
        return jsonify({"message": "Login successful"}), 200
    except Exception as error:
        logging.error("Error logging in: %s", error)
        return jsonify({"message": "Error logging in"}), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)
