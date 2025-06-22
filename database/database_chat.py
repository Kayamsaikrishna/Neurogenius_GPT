import sqlite3
import json
import os
import datetime
import uuid
from pathlib import Path

# Ensure database directory exists
DB_DIR = Path("database")
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "chatdata.db"

def init_db():
    """Initialize the database with necessary tables for chat persistence"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Create chats table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chats (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        name TEXT NOT NULL,
        model TEXT NOT NULL,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    ''')
    
    # Create messages table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id TEXT NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TEXT NOT NULL,
        FOREIGN KEY (chat_id) REFERENCES chats (id) ON DELETE CASCADE
    )
    ''')
    
    # Create usage_logs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS usage_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        action TEXT NOT NULL,
        details TEXT,
        timestamp TEXT NOT NULL
    )
    ''')
    
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        password TEXT NOT NULL,
        created_at TEXT NOT NULL
    )
    ''')
    # Create documents table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS documents (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL,
        name TEXT NOT NULL,
        path TEXT NOT NULL,
        uploaded_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
    )
    ''')
    
    conn.commit()
    conn.close()


# Initialize database on import
init_db()

# ------------------- Logging -------------------

def log_user_action(user_id, action, details=None):
    """Log user actions for tracking usage."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    timestamp = datetime.datetime.now().isoformat()
    
    cursor.execute(
        "INSERT INTO usage_logs (user_id, action, details, timestamp) VALUES (?, ?, ?, ?)",
        (user_id, action, details, timestamp)
    )
    
    conn.commit()
    conn.close()
    
    # Also write to log file for easier viewing
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)
    log_path = log_dir / "app_usage.log"
    
    with open(log_path, "a") as f:
        f.write(f"[{timestamp}] User {user_id}: {action}")
        if details:
            f.write(f" - {details}")
        f.write("\n")

def add_phone_column_to_users():
    """
    Add the 'phone' column to the 'users' table if it doesn't already exist.
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Check if the 'phone' column exists
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    if "phone" not in columns:
        # Add the 'phone' column
        cursor.execute("ALTER TABLE users ADD COLUMN phone TEXT")
        conn.commit()
        print("Added 'phone' column to 'users' table.")

    conn.close()

# ------------------- Chat Management -------------------

def create_chat(user_id, chat_id, chat_name, model="mistral:7b"):
    """Create a new chat session in the database"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    timestamp = datetime.datetime.now().isoformat()
    
    cursor.execute(
        "INSERT INTO chats (id, user_id, name, model, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (chat_id, user_id, chat_name, model, timestamp, timestamp)
    )
    
    conn.commit()
    conn.close()
    
    log_user_action(user_id, "Created chat", f"Chat: {chat_name}, Model: {model}")
    return chat_id

def update_chat_name(chat_id, new_name):
    """Update the name of an existing chat"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    timestamp = datetime.datetime.now().isoformat()
    
    cursor.execute(
        "UPDATE chats SET name = ?, updated_at = ? WHERE id = ?",
        (new_name, timestamp, chat_id)
    )
    
    # Get user_id for logging
    cursor.execute("SELECT user_id FROM chats WHERE id = ?", (chat_id,))
    user_id = cursor.fetchone()[0]
    
    conn.commit()
    conn.close()
    
    log_user_action(user_id, "Renamed chat", f"Chat ID: {chat_id}, New name: {new_name}")
    return True

def update_chat_model(chat_id, new_model):
    """Update the model of an existing chat"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    timestamp = datetime.datetime.now().isoformat()
    
    cursor.execute(
        "UPDATE chats SET model = ?, updated_at = ? WHERE id = ?",
        (new_model, timestamp, chat_id)
    )
    
    # Get user_id for logging
    cursor.execute("SELECT user_id FROM chats WHERE id = ?", (chat_id,))
    user_id = cursor.fetchone()[0]
    
    conn.commit()
    conn.close()
    
    log_user_action(user_id, "Changed chat model", f"Chat ID: {chat_id}, New model: {new_model}")
    return True

def delete_chat(chat_id):
    """Delete a chat and all its messages"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Get user_id for logging before deletion
    cursor.execute("SELECT user_id, name FROM chats WHERE id = ?", (chat_id,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return False
        
    user_id, chat_name = result
    
    # Delete the chat (messages will cascade delete)
    cursor.execute("DELETE FROM chats WHERE id = ?", (chat_id,))
    
    conn.commit()
    conn.close()
    
    log_user_action(user_id, "Deleted chat", f"Chat: {chat_name} (ID: {chat_id})")
    return True


# ------------------- User Management -------------------

def get_chats_by_user(user_id):
    """Get all chats for a specific user"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Return rows as dictionaries
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, name, model, created_at, updated_at FROM chats WHERE user_id = ? ORDER BY updated_at DESC",
        (user_id,)
    )
    
    chats = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    log_user_action(user_id, "Loaded chats", f"Found {len(chats)} chats")
    return chats

# ------------------- Message Management -------------------

def insert_message(chat_id, role, content):
    """Insert a new message into the database"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    timestamp = datetime.datetime.now().isoformat()
    
    cursor.execute(
        "INSERT INTO messages (chat_id, role, content, timestamp) VALUES (?, ?, ?, ?)",
        (chat_id, role, content, timestamp)
    )
    
    # Update the chat's updated_at timestamp
    cursor.execute(
        "UPDATE chats SET updated_at = ? WHERE id = ?",
        (timestamp, chat_id)
    )
    
    # Get user_id for logging
    cursor.execute("SELECT user_id FROM chats WHERE id = ?", (chat_id,))
    user_id = cursor.fetchone()[0]
    
    conn.commit()
    conn.close()
    
    role_type = "user" if role == "user" else "assistant"
    content_preview = content[:30] + "..." if len(content) > 30 else content
    log_user_action(user_id, f"Added {role_type} message", f"Chat ID: {chat_id}, Content: {content_preview}")
    
    return True

def get_messages(chat_id):
    """Get all messages for a specific chat"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT role, content, timestamp FROM messages WHERE chat_id = ? ORDER BY id ASC",
        (chat_id,)
    )
    
    messages = [dict(row) for row in cursor.fetchall()]
    
    # Get user_id for logging
    cursor.execute("SELECT user_id FROM chats WHERE id = ?", (chat_id,))
    result = cursor.fetchone()
    user_id = result["user_id"] if result else "unknown"
    
    conn.close()
    
    log_user_action(user_id, "Retrieved messages", f"Chat ID: {chat_id}, Count: {len(messages)}")
    return messages

def export_chat(chat_id, format="txt"):
    """
    Export a chat to a file format (txt or json).
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get chat info
    cursor.execute("SELECT user_id, name, model FROM chats WHERE id = ?", (chat_id,))
    chat_info = dict(cursor.fetchone())

    # Get messages
    cursor.execute(
        "SELECT role, content, timestamp FROM messages WHERE chat_id = ? ORDER BY id ASC",
        (chat_id,)
    )
    messages = [dict(row) for row in cursor.fetchall()]

    conn.close()

    # Create export directory if it doesn't exist
    export_dir = Path(f"user_documents/{chat_info['user_id']}/exports")
    export_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{chat_info['name'].replace(' ', '_')}_{timestamp}"

    if format.lower() == "json":
        export_data = {
            "chat_id": chat_id,
            "chat_name": chat_info["name"],
            "model": chat_info["model"],
            "exported_at": datetime.datetime.now().isoformat(),
            "messages": messages
        }

        export_path = export_dir / f"{filename}.json"
        with open(export_path, "w", encoding="utf-8") as f:
            json.dump(export_data, f, indent=2)
    else:  # Default to txt
        export_path = export_dir / f"{filename}.txt"
        with open(export_path, "w", encoding="utf-8") as f:
            f.write(f"Chat: {chat_info['name']}\n")
            f.write(f"Model: {chat_info['model']}\n")
            f.write(f"Exported: {datetime.datetime.now().isoformat()}\n")
            f.write("-" * 50 + "\n\n")

            for msg in messages:
                role = "You" if msg["role"] == "user" else "NeuroGenius"
                f.write(f"{role} ({msg['timestamp']}):\n{msg['content']}\n\n")

    log_user_action(
        chat_info["user_id"],
        "Exported chat",
        f"Chat: {chat_info['name']}, Format: {format}, Path: {export_path}"
    )

    return str(export_path)

def get_usage_statistics(user_id, days=30):
    """Get usage statistics for a user over the past X days"""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    # Calculate date threshold
    threshold_date = (datetime.datetime.now() - datetime.timedelta(days=days)).isoformat()
    
    # Get message counts
    cursor.execute("""
        SELECT COUNT(*) as count FROM messages m
        JOIN chats c ON m.chat_id = c.id
        WHERE c.user_id = ? AND m.role = 'user' AND m.timestamp >= ?
    """, (user_id, threshold_date))
    user_messages = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT COUNT(*) as count FROM messages m
        JOIN chats c ON m.chat_id = c.id
        WHERE c.user_id = ? AND m.role = 'assistant' AND m.timestamp >= ?
    """, (user_id, threshold_date))
    assistant_messages = cursor.fetchone()[0]
    
    # Get model usage
    cursor.execute("""
        SELECT model, COUNT(*) as count FROM messages m
        JOIN chats c ON m.chat_id = c.id
        WHERE c.user_id = ? AND m.role = 'assistant' AND m.timestamp >= ?
        GROUP BY model
    """, (user_id, threshold_date))
    model_usage = {row[0]: row[1] for row in cursor.fetchall()}
    
    # Get daily usage
    cursor.execute("""
        SELECT substr(m.timestamp, 1, 10) as day, COUNT(*) as count FROM messages m
        JOIN chats c ON m.chat_id = c.id
        WHERE c.user_id = ? AND m.timestamp >= ?
        GROUP BY day
        ORDER BY day ASC
    """, (user_id, threshold_date))
    daily_usage = {row[0]: row[1] for row in cursor.fetchall()}
    
    conn.close()
    
    stats = {
        "user_messages": user_messages,
        "assistant_messages": assistant_messages,
        "total_messages": user_messages + assistant_messages,
        "model_usage": model_usage,
        "daily_usage": daily_usage,
        "period_days": days
    }
    
    log_user_action(user_id, "Retrieved usage statistics", f"Period: {days} days")
    return stats

def register_user(username, email, phone, password):
    """
    Register a new user in the database.
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Check if the user already exists
    cursor.execute("SELECT * FROM users WHERE email = ? OR phone = ?", (email, phone))
    if cursor.fetchone():
        conn.close()
        raise ValueError("A user with this email or phone number already exists.")

    # Insert the new user
    user_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()
    cursor.execute(
        "INSERT INTO users (id, username, email, phone, password, created_at) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, username, email, phone, password, timestamp)
    )

    conn.commit()
    conn.close()
    return user_id


def get_user_by_identifier(identifier):
    """
    Retrieve a user by username or email.
    """
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # This ensures the result is a dictionary-like object
    cursor = conn.cursor()

    cursor.execute(
        "SELECT * FROM users WHERE username = ? OR email = ?",
        (identifier, identifier)
    )
    user = cursor.fetchone()
    conn.close()

    if user:
        return dict(user)  # Convert to a dictionary
    return None


def update_password(user_id, new_password):
    """
    Update the password for a specific user.
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET password = ? WHERE id = ?",
        (new_password, user_id)
    )

    conn.commit()
    conn.close()
    return True

def get_user_table_info():
    """
    Retrieve information about the 'users' table.
    """
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(users)")
    table_info = cursor.fetchall()
    conn.close()

    return table_info

# ------------------- Document Management -------------------

def upload_document(user_id, document_name, document_path):
    """Upload a document and save its metadata in the database."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    document_id = str(uuid.uuid4())
    timestamp = datetime.datetime.now().isoformat()
    
    cursor.execute(
        "INSERT INTO documents (id, user_id, name, path, uploaded_at) VALUES (?, ?, ?, ?, ?)",
        (document_id, user_id, document_name, document_path, timestamp)
    )
    
    conn.commit()
    conn.close()
    
    log_user_action(user_id, "Uploaded document", f"Document: {document_name}")
    return document_id

def list_documents(user_id):
    """List all documents uploaded by a specific user."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT id, name, path, uploaded_at FROM documents WHERE user_id = ? ORDER BY uploaded_at DESC",
        (user_id,)
    )
    
    documents = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return documents

def delete_document(document_id):
    """Delete a document from the database."""
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    cursor.execute("SELECT user_id, name FROM documents WHERE id = ?", (document_id,))
    result = cursor.fetchone()
    
    if not result:
        conn.close()
        return False
    
    user_id, document_name = result
    
    cursor.execute("DELETE FROM documents WHERE id = ?", (document_id,))
    conn.commit()
    conn.close()
    
    log_user_action(user_id, "Deleted document", f"Document: {document_name}")
    return True