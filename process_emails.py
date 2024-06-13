import json
import psycopg2
from datetime import datetime, timedelta


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
    import pdb;pdb.set_trace()
    cursor.execute(f"SELECT id, snippet, from_address, to_address, subject, message, received_date FROM emails WHERE {where_clause}")
    emails = cursor.fetchall()
    conn.close()

    return emails, target_rule


def apply_actions(email_list, actions, rule_description):
    conn = psycopg2.connect(
        dbname="email_processor",
        user="postgres",
        password="1234",
        host="localhost"
    )
    cursor = conn.cursor()
    import pdb;pdb.set_trace()
    for email in email_list:
        for action in actions:
            if action['type'] == 'Mark as read':
                cursor.execute("UPDATE emails SET is_read = TRUE WHERE id = %s", (email['id'],))
            elif action['type'] == 'Mark as unread':
                cursor.execute("UPDATE emails SET is_read = FALSE WHERE id = %s", (email['id'],))
            elif action['type'] == 'Move Message':
                cursor.execute("UPDATE emails SET folder = %s WHERE id = %s", (action['destination'], email['id']))
        res = cursor.execute("INSERT INTO email_rules (email_id, rule_description) VALUES (%s, %s) ON CONFLICT DO "
                             "NOTHING", (email['id'], rule_description))
    conn.commit()
    conn.close()

