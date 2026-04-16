import psycopg2

conn = psycopg2.connect("dbname=glynk user=glynk password=glynk host=localhost port=5432")
cur = conn.cursor()
cur.execute("SELECT id, origin, target_unit, target_span, role FROM anchors LIMIT 10")
rows = cur.fetchall()
for r in rows:
    print(r)
