import sqlite3, os

db_path = os.path.join('data','estoque.db')
print('DB exists:', os.path.exists(db_path))
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

print('Tables:', [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")])
for tbl in ('orders','order_items','sales','sale_items','products'):
    try:
        c=conn.execute(f'SELECT COUNT(*) FROM {tbl}')
        print(tbl, 'count', c.fetchone()[0])
    except Exception as e:
        print(tbl, 'ERR', e)

print('Latest orders:')
try:
    for r in conn.execute('SELECT id, order_number, status, created_at FROM orders ORDER BY id DESC LIMIT 10;'):
        print(dict(r))
except Exception as e:
    print('orders select error:', e)
