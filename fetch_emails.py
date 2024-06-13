import os
import pickle
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import psycopg2
from datetime import datetime

SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']


def authenticate_gmail():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    service = build('gmail', 'v1', credentials=creds)
    return service


def fetch_emails(service, MAX_BATCH_SIZE):
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], maxResults=MAX_BATCH_SIZE).execute()
    messages = results.get('messages', [])

    emails = []
    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        email_data = {
            'id': msg['id'],
            'snippet': msg['snippet'],
            'payload': msg['payload'],
            'from_address': get_email_address(msg['payload']['headers'], 'From'),
            'to_address': get_email_address(msg['payload']['headers'], 'To'),
            'subject': get_email_header(msg['payload']['headers'], 'Subject'),
            'message': msg['snippet'],
            'received_date': datetime.fromtimestamp(int(msg['internalDate']) / 1000).isoformat()
        }
        emails.append(email_data)
    return emails


def get_email_address(headers, name):
    for header in headers:
        if header['name'] == name:
            return header['value']
    return ''


def get_email_header(headers, name):
    for header in headers:
        if header['name'] == name:
            return header['value']
    return ''


def store_emails(emails):
    conn = psycopg2.connect(
        dbname="email_processor",
        user="postgres",
        password="1234",
        host="localhost"
    )
    cursor = conn.cursor()
    for email in emails:
        cursor.execute(
            '''INSERT INTO emails 
            (id, snippet, payload, from_address, to_address, subject, message, received_date) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) 
            ON CONFLICT (id) DO NOTHING''',
            (email['id'], email['snippet'], json.dumps(email['payload']), email['from_address'], email['to_address'],
             email['subject'], email['message'], email['received_date'])
        )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    service = authenticate_gmail()
    emails = fetch_emails(service, 100)
    store_emails(emails)
