
import sqlite3

# Base temporaire en mémoire : aucune modification de downloads.db
conn = sqlite3.connect(":memory:")

conn.execute("""
    CREATE TABLE test (
        message_id TEXT,
        filename TEXT,
        file_hash TEXT,
        PRIMARY KEY (message_id, filename, file_hash)
    )
""")

# Même message et même nom, mais contenus différents
conn.execute(
    "INSERT INTO test VALUES (?, ?, ?)",
    ("msg-1", "facture.pdf", "hash-A")
)
conn.execute(
    "INSERT INTO test VALUES (?, ?, ?)",
    ("msg-1", "facture.pdf", "hash-B")
)

count = conn.execute("SELECT COUNT(*) FROM test").fetchone()[0]
print(f"Contenus différents acceptés : {count} lignes")

# Tentative d'insertion d'un doublon exact
try:
    conn.execute(
        "INSERT INTO test VALUES (?, ?, ?)",
        ("msg-1", "facture.pdf", "hash-A")
    )
    print("ERREUR : le doublon a été accepté")
except sqlite3.IntegrityError:
    print("Doublon exact rejeté : TEST RÉUSSI")

conn.close()