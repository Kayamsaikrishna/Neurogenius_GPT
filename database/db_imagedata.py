import sqlite3
import datetime
import uuid
from pathlib import Path

# Ensure database directory exists
DB_DIR = Path("database")
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "imagedata.db"

def init_image_db():
    """Initialize the database table for text-to-image history."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    # Create the table if it doesn't exist
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS image_history (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,  -- Add user_id column
            prompt TEXT NOT NULL,
            image_path TEXT NOT NULL,
            timestamp TEXT NOT NULL
        )
    ''')
    # Check if the user_id column exists, and add it if it doesn't
    cursor.execute("PRAGMA table_info(image_history)")
    columns = [column[1] for column in cursor.fetchall()]
    if "user_id" not in columns:
        cursor.execute("ALTER TABLE image_history ADD COLUMN user_id TEXT NOT NULL DEFAULT ''")
    conn.commit()
    conn.close()

init_image_db()

def insert_image_history(user_id, prompt, image_path):
    """
    Insert a new image generation record into the database.
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO image_history (id, user_id, prompt, image_path, timestamp) VALUES (?, ?, ?, ?, ?)",
        (str(uuid.uuid4()), user_id, prompt, image_path, datetime.datetime.now().isoformat())
    )
    conn.commit()
    conn.close()

def get_image_history(user_id):
    """
    Retrieve image generation history for the specified user.
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        "SELECT prompt, image_path FROM image_history WHERE user_id = ?",
        (user_id,)
    )
    records = [{"prompt": row[0], "image_path": row[1]} for row in cursor.fetchall()]
    conn.close()
    return records

def delete_image_history(user_id, prompt):
    """
    Delete an image generation record from the database for the specified user and prompt.
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM image_history WHERE user_id = ? AND prompt = ?",
        (user_id, prompt)
    )
    conn.commit()
    conn.close()
