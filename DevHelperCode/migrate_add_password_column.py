import sqlite3

db_path = "db/database.sqlite"  # Adjust if your path is different

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Check if the column already exists
cursor.execute("PRAGMA table_info(persons);")
columns = [row[1] for row in cursor.fetchall()]

if "password_hash" not in columns:
    print("Adding 'password_hash' column to persons...")
    cursor.execute("ALTER TABLE persons ADD COLUMN password_hash TEXT;")
    conn.commit()
    print("Column added.")
else:
    print("Column already exists.")

conn.close()
