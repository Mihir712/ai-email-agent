import sqlite3
from typing import List, Dict, Any
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'emails.db')


def get_conn():
	conn = sqlite3.connect(DB_PATH)
	return conn


def init_db():
	conn = get_conn()
	cursor = conn.cursor()

	cursor.execute("""
	CREATE TABLE IF NOT EXISTS training_emails(
		id INTEGER PRIMARY KEY,
		category TEXT,
		email TEXT,
		reply TEXT
	)
	""")

	cursor.execute("""
	CREATE TABLE IF NOT EXISTS incoming_emails(
		id INTEGER PRIMARY KEY,
		email TEXT,
		classification TEXT,
		timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
	)
	""")

	cursor.execute("""
	CREATE TABLE IF NOT EXISTS drafts(
		id INTEGER PRIMARY KEY,
		incoming_email_id INTEGER,
		draft TEXT
	)
	""")

	conn.commit()
	conn.close()


def save_incoming(email: str, classification: str) -> int:
	conn = get_conn()
	cursor = conn.cursor()
	cursor.execute(
		"INSERT INTO incoming_emails(email, classification) VALUES(?,?)",
		(email, classification)
	)
	conn.commit()
	incoming_id = cursor.lastrowid
	conn.close()
	return incoming_id


def save_draft(incoming_id: int, draft: str) -> int:
	conn = get_conn()
	cursor = conn.cursor()
	cursor.execute(
		"INSERT INTO drafts(incoming_email_id, draft) VALUES(?,?)",
		(incoming_id, draft)
	)
	conn.commit()
	draft_id = cursor.lastrowid
	conn.close()
	return draft_id


def get_training_emails() -> List[Dict[str, Any]]:
	conn = get_conn()
	cursor = conn.cursor()
	rows = cursor.execute("SELECT id, category, email, reply FROM training_emails").fetchall()
	conn.close()
	return [{"id": r[0], "category": r[1], "email": r[2], "reply": r[3]} for r in rows]


# initialize DB on import
init_db()