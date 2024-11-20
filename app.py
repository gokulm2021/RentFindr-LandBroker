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
from bson.objectid import ObjectId
from PIL import Image
import re
import os
from uuid import uuid4



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



def resize_image(image_path):
    with Image.open(image_path) as img:
        target_width = 600  # Example width
        target_height = 800  # Example height
        img = img.resize((target_width, target_height), Image.LANCZOS)
        img.save(image_path)


# Function to resize agent photo with specific dimensions
def resize_agent_photo(image_path):
    with Image.open(image_path) as img:
        img = img.convert("RGB")  # Ensure it's in RGB format
        target_width = 800  # Example width
        target_height = 896  # Example height
        img = img.resize((target_width, target_height), Image.Resampling.LANCZOS)
        img.save(image_path)



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
properties_collection = db.properties

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
        
    # Fetch the latest property
    latest_property = db['properties'].find().sort('_id', -1).limit(1)
    latest_property = list(latest_property)  # Convert to list
    if latest_property:
        latest_property = latest_property[0]  # Extract the first element
    else:
        latest_property = {}
    
    # Pass latest_property to the template
    return render_template('index.html', user_logged_in=user_logged_in, username=username, looking_for=looking_for, latest_property=latest_property)

@app.route('/logout')
def logout():
    # session.pop('username', None)  # Remove user from session
    # return redirect('/')
    # # Clear the session
    session.pop('role', None)  # Specifically remove 'role' from session
    session.pop('email', None)  # Remove email as well, if necessary
    # Print the session to debug
    print(f"Session after logout: {session}")
    session.clear()  # This will remove all session data, including the 'role'
    return redirect(url_for('index'))  # Redirect to the homepage or login page

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
    properties = properties_collection.find()  # Fetch all properties from MongoDB
    tamilnadu_districts = [
    "Ariyalur", "Chengalpattu", "Chennai", "Coimbatore", "Cuddalore", 
    "Dharmapuri", "Dindigul", "Erode", "Kallakurichi", "Kancheepuram", 
    "Karur", "Krishnagiri", "Madurai", "Mayiladuthurai", "Nagapattinam", 
    "Namakkal", "Nilgiris", "Perambalur", "Pudukottai", "Ramanathapuram", 
    "Ranipet", "Salem", "Sivagangai", "Tenkasi", "Thanjavur", "Theni", 
    "Thoothukudi", "Tiruchirappalli", "Tirunelveli", "Tirupathur", "Tiruppur", 
    "Tiruvallur", "Tiruvannamalai", "Tiruvarur", "Vellore", "Viluppuram", 
    "Virudhunagar"
]
    return render_template('property-grid.html', tamilnadu_districts=tamilnadu_districts, user_logged_in=user_logged_in, username=username, looking_for=looking_for, properties=properties)



@app.route('/property/<property_id>', endpoint='property_detail')
def property_detail(property_id):
    # Retrieve the logged-in user's email from the session
    user_email = session.get('email')
    # Retrieve the property from the database
    property = properties_collection.find_one({'_id': ObjectId(property_id)})
    user_logged_in = 'username' in session  # Check if the user is logged in
    username = session.get('username')  # Get the username from the session
    looking_for = session.get('looking_for')  # Get the 'Looking For' data from the session
    is_owner = user_email == property.get('seller_email') if property else False
    # Check if the property exists
    if not property:
        return "Property not found", 404

    # Get the agent information if it's part of the property document
    agent = property.get('agent', {})  # Default to empty dictionary if no agent field exists

    # Render the template, passing both property and agent data
    return render_template('property-single.html', property=property, agent=agent, user_logged_in=user_logged_in, username=username, looking_for=looking_for, is_owner=is_owner)



@app.route('/property/<property_id>', methods=['GET'])
def property_single(property_id):
    # Retrieve the property from the database
    property = properties_collection.find_one({'_id': ObjectId(property_id)})

    # Check if the property exists
    if not property:
        return "Property not found", 404

    # Ensure agent data is present (use .get to avoid key errors)
    agent = property.get('agent', {})
    agent_image = agent.get('photo', '')  # Assuming the agent photo path is stored in 'photo'

    # Get the list of property images
    property_images = property.get('images', [])

    # Render the template, passing the property and agent data
    return render_template('property-single.html', property=property, agent=agent, property_images=property_images, agent_image=agent_image)




@app.route('/delete-property/<property_id>', methods=['POST'])
def delete_property(property_id):
    # Check if the user is logged in and is a Seller
    if 'role' not in session or session['role'] != 'Seller':
        return jsonify({"message": "You are not authorized to delete this property"}), 403  # Return error if unauthorized

    # Ensure the property exists and belongs to the logged-in user
    property = properties_collection.find_one({"_id": ObjectId(property_id)})
    if property['seller_email'] != session['email']:
        return jsonify({"message": "You are not authorized to delete this property"}), 403  # Unauthorized access

    # Delete the property
    properties_collection.delete_one({"_id": ObjectId(property_id)})
    return jsonify({"message": "Property deleted successfully"}), 200  # Return success message







@app.route('/property-grid')
def property_grid():
    user_logged_in = 'username' in session  # Check if the user is logged in
    username = session.get('username')  # Get the username from the session
    looking_for = session.get('looking_for')  # Get the 'Looking For' data from the session
    # Fetch properties from the database
    properties = properties_collection.find()
    
    # Render the property-grid template with the properties
    return render_template('property-grid.html', properties=properties,  user_logged_in=user_logged_in, username=username, looking_for=looking_for)












@app.route('/contact.html')
def contact():
    user_logged_in = 'username' in session  # Check if the user is logged in
    username = session.get('username')  # Get the username from the session
    looking_for = session.get('looking_for')  # Get the 'Looking For' data from the session
    return render_template('contact.html', user_logged_in=user_logged_in, username=username, looking_for=looking_for)

@app.route('/dashboard')
def dashboard():
    if 'email' not in session:  # Check for unique email in the session
        return redirect('/login')  # Redirect to login if user is not logged in

    email = session.get('email')  # Retrieve the logged-in user's email
    looking_for = session.get('looking_for')  # Retrieve 'looking_for' from session

    # Retrieve user details from the database using email
    user = users_collection.find_one({"email": email})

    if user is None:
        return jsonify({"message": "User not found"}), 404

    # Pass user details to the template
    return render_template(
        'dashboard.html',
        username=user.get('fullName'),  # Use the full name from the database
        user_email=user.get('email'),
        looking_for=looking_for,
        profile_picture=user.get('profilePicture')  # Pass the profile picture filename
    )




@app.route('/update-email', methods=['Post'])
def update_email():
    if 'email' not in session:  # Ensure the email is used as a unique identifier
        return jsonify({"message": "Unauthorized"}), 401

    try:
        # Get the new email from the request body
        data = request.get_json()
        new_email = data.get("email")

        # Validate the new email
        if not new_email:
            return jsonify({"message": "New email is required"}), 400

        # Update the user's email in the database
        result = users_collection.update_one(
            {"email": session['email']},  # Match the current email in the session
            {"$set": {"email": new_email}}  # Set the new email
        )

        # Check if the email was updated
        if result.modified_count == 0:
            return jsonify({"message": "No changes made, email may be the same."}), 400

        # Update the session with the new email
        session['email'] = new_email

        return jsonify({"message": "Email updated successfully"}), 200

    except Exception as e:
        logging.error(f"Error updating email: {e}")
        return jsonify({"message": "An error occurred while updating the email"}), 500


@app.route('/update-password', methods=['POST'])
def update_password():
    # Check if email exists in session
    if 'email' not in session:
        return jsonify({"message": "Unauthorized"}), 401

    # Log current session user email for debugging
    print(f"Current session email: {session['email']}")
    
    data = request.get_json()
    new_password = data.get("password")
    
    if not new_password:
        return jsonify({"message": "Password is required"}), 400

    # Find the user using the email from session
    user = users_collection.find_one({"email": session['email']})
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    # Update the user's password in the database
    result = users_collection.update_one({"email": session['email']}, {"$set": {"password": new_password}})
    
    if result.matched_count == 0:
        return jsonify({"message": "User not found"}), 404
    if result.modified_count == 0:
        return jsonify({"message": "No changes made"}), 400

    return jsonify({"message": "Password updated successfully"}), 200



@app.route('/delete-account', methods=['DELETE'])
def delete_account():
    if 'email' not in session:  # Ensure the email is used as a unique identifier
        return jsonify({"message": "Unauthorized"}), 401

    try:
        # Delete the user from the database based on their unique email
        result = users_collection.delete_one({"email": session['email']})

        if result.deleted_count == 0:
            return jsonify({"message": "Account not found"}), 404

        # Clear the session
        session.clear()

        return jsonify({"message": "Account deleted successfully"}), 200

    except Exception as e:
        logging.error(f"Error deleting account: {e}")
        return jsonify({"message": "An error occurred while deleting the account"}), 500

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

@app.route('/add-property', methods=['GET', 'POST'])
def add_property():
    # Check if the user is logged in and has a Seller role
    if 'role' not in session or session['role'] != 'Seller':
        return redirect(url_for('login'))  # Redirect to login if not logged in as a Seller
    
    if request.method == 'POST':
        # Collect property data from the form
        property_name = request.form.get('propertyName')
        location = request.form.get('location')
        pincode = request.form.get('pincode')  # Get the pincode from the form
        price = request.form.get('price')
        type_of_property = request.form.get('type')
        description = request.form.get('description')
        sale_status = request.form.get('sale_status')
        area = request.form.get('area')
        beds = request.form.get('beds')
        baths = request.form.get('baths')
        yards = request.form.get('yards')
        
         # Collect Google Maps embed link
        google_map_link = request.form.get('googleMapLink')

        # Validate the Google Maps embed link
        map_link_pattern = r"^https://www\.google\.com/maps/embed\?.+$"
        if not re.match(map_link_pattern, google_map_link):
            return jsonify({"error": "Invalid Google Maps Embed Link. Please provide a correct embed URL."}), 400

        # Handle amenities (predefined + custom)
        amenities = request.form.getlist('amenities')
        custom_amenities = request.form.get('customAmenities')
        if custom_amenities:
            custom_amenities_list = [amenity.strip() for amenity in custom_amenities.split(',')]
            amenities.extend(custom_amenities_list)

        # Agent information
        agent_name = request.form.get('agentName')
        agent_description = request.form.get('agentDescription')
        agent_phone = request.form.get('agentPhone')
        agent_email = request.form.get('agentEmail')
        
        # Handle agent photo upload
        agent_photo = None
        if 'agentPhoto' in request.files:
            agent_photo_file = request.files['agentPhoto']
            if agent_photo_file and allowed_file(agent_photo_file.filename):
                agent_image_folder = 'static/agents'
                if not os.path.exists(agent_image_folder):
                    os.makedirs(agent_image_folder)
                
                agent_photo_filename = secure_filename(agent_photo_file.filename)
                agent_photo_path = os.path.join(agent_image_folder, agent_photo_filename)
                agent_photo_file.save(agent_photo_path)
                resize_agent_photo(agent_photo_path)  # Resize specifically for agent photos
                agent_photo = f"/static/agents/{agent_photo_filename}"

        # Seller email from session
        seller_email = session.get('email')
        if not seller_email:
            return jsonify({"message": "You need to be logged in as a Seller to add a property"}), 403

        # Handle property images upload
        images = []
        if 'images' in request.files:
            image_folder = 'static/images'
            if not os.path.exists(image_folder):
                os.makedirs(image_folder)


            for image in request.files.getlist('images'):
                if image and allowed_file(image.filename):
                    filename = secure_filename(image.filename)
                    image_path = os.path.join(image_folder, filename)
                    image.save(image_path)
                    resize_image(image_path)
                    images.append(f"/static/images/{filename}")

        # Create the property dictionary to save in the database
        new_property = {
            'name': property_name,
            'location': location,
            'pincode': pincode,  # Save the pincode
            'google_map_link': google_map_link,  # Save the Google Maps embed link
            'price': price,
            'type': type_of_property,
            'sale_status': sale_status,
            'description': description,
            'area': area,
            'beds': beds,
            'baths': baths,
            'yards': yards,
            'images': images,
            "seller_email": session['email'],  # set the logged-in user's email as seller_email
            'agent': {
                'name': agent_name,
                'description': agent_description,
                'phone': agent_phone,
                'email': agent_email,
                'photo': agent_photo
            },
            'amenities': amenities
        }

        # Insert the new property into MongoDB
        properties_collection = db["properties"]
        properties_collection.insert_one(new_property)
        
        # Redirect after successful insertion
        return redirect(url_for('property_grid'))

    return render_template('add-property.html')






# @app.route('/upload_property_image', methods=['POST'])
# def upload_property_image():
#     if 'image' not in request.files:
#         return "No file part"
#     file = request.files['image']
#     if file.filename == '':
#         return "No selected file"
#     if file:
#         # Save the uploaded file
#         filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
#         file.save(filepath)

#         # Process the image
#         is_intro_slide = request.form.get('is_intro_slide', 'false').lower() == 'true'
#         process_image(filepath, is_intro_slide=is_intro_slide)

#         # Return response or save the image details in the database
#         return "Image processed and saved."







@app.route('/login.html')
def login():
    return render_template('login.html')

@app.route('/signup.html')
def signup():
    return render_template('signup.html')

# Route to display properties
@app.route('/properties')
def properties():
    all_properties = properties_collection.find()
    return render_template('properties.html', properties=all_properties)

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
    role = data.get("role")  # Collect role option

    logging.debug(f"Full Name: {full_name}, Email: {email}, Looking For: {looking_for}, Role: {role}")

    # Additional checks
    if not email:
        return jsonify({"message": "Email is required"}), 400

    if password != confirm_password:
        return jsonify({"message": "Passwords do not match"}), 400

    if role not in ["Seller", "User"]:
        return jsonify({"message": "Invalid role selected"}), 400

    # Save the profile picture with a unique filename
    if profile_picture and allowed_file(profile_picture.filename):
        original_filename = secure_filename(profile_picture.filename)
        unique_filename = f"{uuid4().hex}_{original_filename}"  # Generate a unique filename
        profile_picture.save(os.path.join(app.config['UPLOAD_FOLDER'], unique_filename))
    else:
        unique_filename = None  # Handle the case when the profile picture is not provided

    try:
        # Insert new user data into the 'users' collection
        users_collection = db["users"]

        # Check if email already exists
        existing_user = users_collection.find_one({"email": email})
        if existing_user:
            return jsonify({"message": "Email already registered"}), 400

        # Create a new user document
        new_user = {
            "fullName": full_name,
            "email": email,
            "password": password,
            "lookingFor": looking_for,
            "role": role,
            "profilePicture": unique_filename  # Store the unique filename in your database
        }

        # Insert user into the database and get their unique `_id`
        result = users_collection.insert_one(new_user)
        user_id = str(result.inserted_id)  # MongoDB-generated unique user ID

        logging.debug(f"New User: {new_user}")  # Log the new user details

        # Save the user's info in the session
        session.clear()  # Clear any existing session data
        session['user_id'] = user_id  # Use the unique user ID for session tracking
        session['email'] = email  # Use email as a secondary identifier
        session['role'] = role  # Save the role in the session
        session['looking_for'] = looking_for
        session['username'] = full_name  # Optionally save the full name

        return jsonify({"message": "User registered successfully"}), 201
    except Exception as error:
        logging.error("Error registering user: %s", error)
        return jsonify({"message": "Error registering user"}), 500




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
        session['username'] = user.get('fullName')  # Store the user's full name in the session
        session['email'] = user.get('email')  # Store the user's email in the session
        session['role'] = user.get('role')  # Store the user's role in the session (Seller/Buyer)
    
        # Send a success response
        return jsonify({"message": "Login successful"}), 200
    except Exception as error:
        logging.error("Error logging in: %s", error)
        return jsonify({"message": "Error logging in"}), 500



if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(host='0.0.0.0', port=port, debug=True)
