import sqlite3

conn = sqlite3.connect("db/database.sqlite")  # adjust path if needed
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(persons);")
for col in cursor.fetchall():
    print(col)

conn.close()
