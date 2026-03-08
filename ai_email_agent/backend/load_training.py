import json
import os
from . import database


def load_training_from_file(path: str):
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    conn = database.get_conn()
    cursor = conn.cursor()

    for item in data:
        # Skip if identical entry exists
        cursor.execute(
            "SELECT id FROM training_emails WHERE email = ? AND reply = ?",
            (item.get('email'), item.get('reply'))
        )
        if cursor.fetchone():
            continue

        cursor.execute(
            "INSERT INTO training_emails(category,email,reply) VALUES(?,?,?)",
            (item.get('category'), item.get('email'), item.get('reply'))
        )

    conn.commit()
    conn.close()


def load_all_training():
    base = os.path.join(os.path.dirname(__file__), '..', 'training data')
    if not os.path.exists(base):
        base = os.path.join(os.path.dirname(__file__), '..', 'training_data')

    for fname in os.listdir(base):
        if fname.endswith('.json'):
            load_training_from_file(os.path.join(base, fname))


if __name__ == '__main__':
    load_all_training()