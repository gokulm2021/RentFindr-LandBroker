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

