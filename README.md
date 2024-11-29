# Flask Web Application with Machine Learning

This is a Flask-based web application that integrates MongoDB, machine learning (using RandomForestRegressor), email functionality (via Flask-Mail), and file uploads. It also supports CORS and uses environment variables stored in a `.env` file for sensitive information.

## Features

- **Machine Learning**: Uses `RandomForestRegressor` from scikit-learn for predictions.
- **MongoDB Integration**: Stores and retrieves data using MongoDB.
- **File Uploads**: Secure file upload functionality with `werkzeug`.
- **Email Functionality**: Send emails using Flask-Mail.
- **CORS Support**: Cross-origin resource sharing enabled for API access.
- **Environment Configuration**: Manage environment variables using a `.env` file.

## Installation

### Prerequisites

- Python 3.x
- MongoDB (local or cloud instance like MongoDB Atlas)

### Steps

1. Clone the repository:

    ```bash
    git clone https://github.com/your-username/your-repository.git
    ```

2. Navigate into the project folder:

    ```bash
    cd your-repository
    ```

3. Create and activate a virtual environment:

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
    ```

4. Install the dependencies:

    ```bash
    pip install -r requirements.txt
    ```

5. Set up the `.env` file for sensitive data (MongoDB URI, email credentials, etc.):

    ```
    MONGO_URI=mongodb://localhost:27017/your-database
    MAIL_USERNAME=your-email@example.com
    MAIL_PASSWORD=your-email-password
    ```

## Running the Application

1. Ensure MongoDB is running (or use a cloud MongoDB instance).
2. Start the Flask app:

    ```bash
    python app.py
    ```

3. Visit `http://127.0.0.1:5000/` in your browser to access the application.

## Project Structure


### Explanation of Project Structure:
- **app.py**: The main file for your Flask application that contains all the routing logic and integrates the machine learning model, MongoDB, file uploads, etc.
- **requirements.txt**: A list of Python libraries and dependencies needed for the application.
- **.env**: A file containing sensitive information like your MongoDB URI and email credentials.
- **templates/**: Folder containing HTML files (rendered by Flask) for your frontend.
- **static/**: Folder for static assets such as CSS, JavaScript, and images.
- **uploads/**: Folder where user-uploaded files are stored.
- **logs/**: Directory to store application logs, useful for debugging and monitoring.
- **README.md**: Project documentation, which is the file you’re reading now.

This is a complete README file including the project structure! You can directly copy-paste this into your `README.md` on GitHub.
