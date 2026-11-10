import sqlite3

db = sqlite3.connect("data/fidomek_dev.db")

tables = db.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    ORDER BY name
""").fetchall()

print("=== TABLES ===")
for table in tables:
    print(table[0])

print("\n=== ALEMBIC VERSION ===")
print(db.execute("SELECT version_num FROM alembic_version").fetchall())

print("\n=== FOREIGN KEYS ===")
for (table_name,) in tables:
    if table_name != "alembic_version":
        foreign_keys = db.execute(
            f'PRAGMA foreign_key_list("{table_name}")'
        ).fetchall()

        print(f"\n{table_name}:")
        for fk in foreign_keys:
            print(f"  {fk}")

db.close()
