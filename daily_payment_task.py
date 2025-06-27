# daily_payment_task.py
import psycopg2
from datetime import datetime, timedelta, date

conn = psycopg2.connect(
    dbname="shelter",
    user="postgres",
    password="root",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

today = date.today()
tomorrow = today + timedelta(days=1)

cursor.execute("""
    SELECT sub_id, amount FROM subscriptions
    WHERE cancel_date IS NULL AND DATE(next_payment_date) = %s
""", (today,))

subs = cursor.fetchall()

for sub_id, amount in subs:
    cursor.execute("""
        INSERT INTO payments (fk_sub_id, payment_date, amount)
        VALUES (%s, %s, %s)
    """, (sub_id, datetime.now(), amount))

    cursor.execute("""
        UPDATE subscriptions
        SET next_payment_date = %s
        WHERE sub_id = %s
    """, (tomorrow, sub_id))

conn.commit()
conn.close()

#print(f"\u2705 Выполнено: {len(subs)} платежей обработано на {today.strftime('%Y-%m-%d')}")
