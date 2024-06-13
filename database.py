import psycopg2


def setup_database():
    conn = psycopg2.connect(
        dbname="email_processor",
        user="postgres",
        password="1234",
        host="localhost"
    )
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS emails (
            id TEXT PRIMARY KEY, 
            snippet TEXT, 
            payload TEXT,
            from_address TEXT,
            to_address TEXT,
            subject TEXT,
            message TEXT,
            received_date TIMESTAMP,
            is_read BOOLEAN DEFAULT FALSE,
            folder TEXT DEFAULT 'Inbox'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS email_rules (
            email_id TEXT,
            rule_description TEXT,
            PRIMARY KEY (email_id, rule_description),
            FOREIGN KEY (email_id) REFERENCES emails(id)
        )
    ''')
    conn.commit()
    conn.close()


if __name__ == "__main__":
    setup_database()
