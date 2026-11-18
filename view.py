import sqlite3

conn = sqlite3.connect("edufuture.db")
for (t,) in conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name != 'sqlite_sequence'"
):
  print(f"\n[{t.upper()}]")
  for r in conn.execute(f"SELECT * FROM {t}").fetchall():
    print(" ", r)
conn.close()