# Email Processor

## Description
This Flask application fetches emails from Gmail using the Gmail API, stores them in a PostgreSQL database, and allows processing of emails based on predefined rules.

## Prerequisites
Before running the application, ensure you have the following installed:
- Python (version 3.7 or higher)
- PostgreSQL
- Google API credentials (`credentials.json`) for accessing Gmail API

## Installation Steps

1. **Clone the Repository**
   ```bash
   git clone https://github.com/Manan2506/Email-Processor.git
   cd email-processor
2. **Set Up Virtual Environment (Optional but Recommended)**

   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`   

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   
4. **Set Up Database**

   - Ensure PostgreSQL is running.
   - Modify database.py to set up your database schema if needed.


5. **Obtain Google API Credentials**

   - Visit [Google Cloud Console](https://console.cloud.google.com/) and create a new project or select an existing one.
   - Navigate to APIs & Services > Credentials.
   - Click on "Create credentials" and select "OAuth client ID".
   - Choose "Desktop app" as the application type if running locally and click "Create".
   - Download the `credentials.json` file and place it in the root directory of the project.
   
## Running the Application

6. Run the Flask Application

   ```bash
   python app.py
  - The application will start running on `http://localhost:5000/`.

## API Endpoints

- Fetch and Store Emails

  - Endpoint: `POST /fetch_emails`
  - Description: Fetches emails from Gmail and stores them in the database.
  - Request Body: JSON with batch_size parameter.
  
   ```bash
   curl -X POST http://localhost:5000/fetch_emails -H "Content-Type: application/json" -d '{"batch_size": 50}'

- Process Emails
  - Endpoint: `GET /process_emails`
  - Description: Applies a rule to fetch and process emails based on `rule_description` query parameter.
  
   ```bash
   curl -X GET 'http://localhost:5000/process_emails?rule_description=Rule 2'
