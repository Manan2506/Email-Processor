import json
import psycopg2
from datetime import datetime, timedelta
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import pickle
import argparse


def load_rules():
    with open('rules.json', 'r') as file:
        rules = json.load(file)
    return rules


def evaluate_condition_sql(condition):
    field = condition['field']
    predicate = condition['predicate']
    value = condition['value']

    if field in ['from_address', 'to_address', 'Subject', 'Message']:
        if predicate == 'Contains':
            return f"{field.lower()} LIKE '%{value}%'"
        elif predicate == 'Does not Contain':
            return f"{field.lower()} NOT LIKE '%{value}%'"
        elif predicate == 'Equals':
            return f"{field.lower()} = '{value}'"
        elif predicate == 'Does not Equal':
            return f"{field.lower()} != '{value}'"
    elif field == 'received_date':
        date_value = (datetime.now() - timedelta(days=int(value.split()[0]))).strftime('%Y-%m-%d %H:%M:%S')
        if predicate == 'Less than':
            return f"received_date < '{date_value}'"
        elif predicate == 'Greater than':
            return f"received_date > '{date_value}'"

    return ''


def fetch_emails_by_rule(rule_description):
    rules = load_rules()
    target_rule = next((rule for rule in rules if rule['description'] == rule_description), None)
    if not target_rule:
        return []

    conditions = target_rule['conditions']
    overall_predicate = target_rule['type']

    sql_conditions = [evaluate_condition_sql(cond) for cond in conditions]
    if overall_predicate == 'All':
        where_clause = ' AND '.join(sql_conditions)
    else:
        where_clause = ' OR '.join(sql_conditions)

    conn = psycopg2.connect(
        dbname="email_processor",
        user="postgres",
        password="1234",
        host="localhost"
    )
    cursor = conn.cursor()
    cursor.execute(
        f"SELECT id, snippet, from_address, to_address, subject, message,"
        f" received_date FROM emails WHERE {where_clause}")
    emails = cursor.fetchall()
    conn.close()

    return emails, target_rule


def authenticate_gmail():
    SCOPES = ['https://www.googleapis.com/auth/gmail.modify']
    creds = None
    token_path = 'token.pickle'
    credentials_path = 'credentials.json'

    if os.path.exists(token_path):
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
            except Exception as e:
                print(f"Error refreshing credentials: {e}")
                os.remove(token_path)
                creds = None
        if not creds:
            flow = InstalledAppFlow.from_client_secrets_file(credentials_path, SCOPES)
            creds = flow.run_local_server(port=0)
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)

    return build('gmail', 'v1', credentials=creds)


def apply_actions(email_list, actions, rule_description):
    service = authenticate_gmail()
    conn = psycopg2.connect(
        dbname="email_processor",
        user="postgres",
        password="1234",
        host="localhost"
    )
    cursor = conn.cursor()

    for email in email_list:
        for action in actions:
            if action['type'] == 'Mark as read':
                mark_as_read(service, email['id'])
            elif action['type'] == 'Mark as unread':
                mark_as_unread(service, email['id'])
            elif action['type'] == 'Move Message':
                move_message(service, email['id'], action['destination'])
        cursor.execute("INSERT INTO email_rules (email_id, rule_description) VALUES (%s, %s) ON CONFLICT DO NOTHING",
                       (email['id'], rule_description))

    conn.commit()
    conn.close()


def mark_as_read(service, msg_id):
    res = service.users().messages().modify(userId='me', id=msg_id, body={'removeLabelIds': ['UNREAD']}).execute()
    print(f"Message id {msg_id} Marked as read", res)


def mark_as_unread(service, msg_id):
    res = service.users().messages().modify(userId='me', id=msg_id, body={'addLabelIds': ['UNREAD']}).execute()
    print(f"Message id {msg_id} Marked as unread", res)

def move_message(service, msg_id, destination):
    labels = {
        'Inbox': 'INBOX',
        'Important': 'IMPORTANT',
        'Work': 'CATEGORY_WORK',
        'Projects': 'CATEGORY_PROJECTS',
        'Promotions': 'CATEGORY_PROMOTIONS',
        'Archive': 'CATEGORY_ARCHIVE',
        'Today': 'CATEGORY_TODAY'
    }
    if destination in labels:
        label_id = labels[destination]
        res = service.users().messages().modify(userId='me', id=msg_id, body={'addLabelIds': [label_id]}).execute()
        print(f"Message id {msg_id} moved to {destination}", res)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process emails based on rules.')
    parser.add_argument('rule_description', type=str, help='The description of the rule to apply.')
    args = parser.parse_args()

    emails, target_rule = fetch_emails_by_rule(args.rule_description)

    email_list = []
    for email in emails:
        email_dict = {
            'id': email[0],
            'snippet': email[1],
            'from_address': email[2],
            'to_address': email[3],
            'subject': email[4],
            'message': email[5],
            'received_date': email[6]
        }
        email_list.append(email_dict)

    if email_list:
        apply_actions(email_list, target_rule['actions'], args.rule_description)
