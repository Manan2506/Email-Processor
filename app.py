from flask import Flask, jsonify, request

from database import setup_database
from fetch_emails import authenticate_gmail, fetch_emails, store_emails
from process_emails import fetch_emails_by_rule, apply_actions

app = Flask(__name__)


@app.route('/fetch_emails', methods=['POST'])
def fetch_and_store_emails():
    try:
        batch_size = request.json.get('batch_size')
        service = authenticate_gmail()
        emails = fetch_emails(service, batch_size)
        setup_database()
        store_emails(emails)
        return jsonify({"message": "Emails fetched and stored successfully!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/process_emails', methods=['GET'])
def apply_rule():
    try:
        rule_description = request.args.get('rule_description')
        emails, target_rule = fetch_emails_by_rule(rule_description)

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
            email_list += [email_dict]
        if email_list:
            apply_actions(email_list, target_rule['actions'], rule_description)
        return jsonify(email_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
