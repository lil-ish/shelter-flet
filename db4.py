import psycopg2
from datetime import date

conn = psycopg2.connect(
    dbname="shelter",
    user="postgres",
    password="root",
    host="localhost",
    port="5432"
)
cursor = conn.cursor()

def get_user_id_by_name(full_name):
    cursor.execute("SELECT user_id FROM users WHERE full_name = %s", (full_name,))
    result = cursor.fetchone()
    return result[0] if result else None

def add_task_to_db(description, execution_date, status, user_id):
    cursor.execute(
        "INSERT INTO tasks (description, execution_date, status, fk_user_id) VALUES (%s, %s, %s, %s)",
        (description, execution_date, status, user_id)
    )
    conn.commit()

def delete_task_from_db(task_id):
    cursor.execute("DELETE FROM tasks WHERE task_id = %s", (task_id,))
    conn.commit()

def update_task_in_db(task_id, description, execution_date, status, user_id):
    cursor.execute(
        "UPDATE tasks SET description=%s, execution_date=%s, status=%s, fk_user_id=%s WHERE task_id=%s",
        (description, execution_date, status, user_id, task_id)
    )
    conn.commit()

def get_all_users():
    cursor.execute("SELECT user_id, full_name FROM users")
    return cursor.fetchall()

def get_reports_from_db():
    cursor.execute("""
        SELECT r.report_id, r.publication_date, r.period, r.document_link, u.full_name 
        FROM reports r
        LEFT JOIN users u ON r.fk_user_id = u.user_id
        ORDER BY r.publication_date DESC
    """)
    return cursor.fetchall()

def add_report_to_db(publication_date, period, document_link, user_id):
    cursor.execute(
        "INSERT INTO reports (publication_date, period, document_link, fk_user_id) VALUES (%s, %s, %s, %s)",
        (publication_date, period, document_link, user_id)
    )
    conn.commit()

def delete_report_from_db(report_id):
    cursor.execute("DELETE FROM reports WHERE report_id = %s", (report_id,))
    conn.commit()

def update_animal_health_in_db(animal_id, health_status):
    cursor.execute("""
        UPDATE animal
        SET health_status=%s
        WHERE animal_id=%s
    """, (health_status, animal_id))
    conn.commit()

def get_animal_health_logs(animal_id):
    cursor.execute("""
        SELECT date, note FROM animal_vet
        WHERE fk_animal_id = %s
        ORDER BY date DESC
    """, (animal_id,))
    return cursor.fetchall()

def add_animal_health_log(animal_id, vet_id, note):
    cursor.execute("""
        INSERT INTO animal_vet (fk_animal_id, fk_user_id, date, note)
        VALUES (%s, %s, CURRENT_DATE, %s)
    """, (animal_id, vet_id, note))
    conn.commit()

def get_tasks_from_db():
    cursor.execute("SELECT task_id, description, execution_date, status FROM tasks")
    return cursor.fetchall()

def get_animals_from_db():
    cursor.execute("""
        SELECT animal_id, name, gender, health_status, care_status, admission_date, 
               birth_date, character_description, reason, photo
        FROM animal
        ORDER BY admission_date DESC
    """)
    return cursor.fetchall()

def add_animal_to_db(name, gender, health_status, care_status, admission_date, birth_date, character_description, reason, photo_bytes=None):
    sql = """
        INSERT INTO animal (name, gender, health_status, care_status, admission_date, birth_date, character_description, reason, photo)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        RETURNING animal_id
    """
    cursor.execute(sql, (
        name, gender, health_status, care_status,
        admission_date, birth_date, character_description, reason,
        psycopg2.Binary(photo_bytes) if photo_bytes else None
    ))
    animal_id = cursor.fetchone()[0]
    conn.commit()
    return animal_id

def update_animal_in_db(animal_id, name, gender, health_status, care_status, admission_date, birth_date, character_description, reason, photo_bytes=None):
    if photo_bytes is not None:
        sql = """
            UPDATE animal SET
                name=%s, gender=%s, health_status=%s, care_status=%s,
                admission_date=%s, birth_date=%s, character_description=%s,
                reason=%s, photo=%s
            WHERE animal_id=%s
        """
        cursor.execute(sql, (
            name, gender, health_status, care_status,
            admission_date, birth_date, character_description, reason,
            psycopg2.Binary(photo_bytes),
            animal_id
        ))
    else:
        sql = """
            UPDATE animal SET
                name=%s, gender=%s, health_status=%s, care_status=%s,
                admission_date=%s, birth_date=%s, character_description=%s,
                reason=%s
            WHERE animal_id=%s
        """
        cursor.execute(sql, (
            name, gender, health_status, care_status,
            admission_date, birth_date, character_description, reason,
            animal_id
        ))
    conn.commit()

def delete_animal_from_db(animal_id):
    try:
        cursor.execute("DELETE FROM animal WHERE animal_id = %s", (animal_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e

def get_connection():
    return psycopg2.connect(
        dbname="shelter",
        user="postgres",
        password="root",
        host="localhost",
        port="5432"
    )

def get_all_animals(gender=None, age_range=None, health=None, care=None):
    conn = psycopg2.connect(
        dbname="shelter",
        user="postgres",
        password="root",
        host="localhost",
        port="5432"
    )
    cur = conn.cursor()

    query = """
        SELECT animal_id, name, gender, health_status, care_status, admission_date, birth_date,
               character_description, reason, photo
        FROM animal
    """
    params = []
    conditions = []
    
    if gender:
        conditions.append("gender = %s")
        params.append(gender.lower())

    if health:
        conditions.append("health_status = %s")
        params.append(health)

    if care:
        conditions.append("care_status = %s")
        params.append(care)

    if age_range:
        today = date.today()
        min_birth_date = today.replace(year=today.year - int(age_range[1]))
        max_birth_date = today.replace(year=today.year - int(age_range[0]))
        conditions.append("birth_date BETWEEN %s AND %s")
        params.append(min_birth_date)
        params.append(max_birth_date)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    
    query += " ORDER BY admission_date DESC"

    try:
        cur.execute(query, tuple(params))
        results = cur.fetchall()
    except Exception as e:
        print("Ошибка выполнения запроса:", e)
        results = []
    finally:
        cur.close()
        conn.close()

    return results

def authenticate_user(email_val, password_val):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "SELECT role, user_id, deleted_at FROM users WHERE email = %s AND password = %s",
        (email_val, password_val)
    )
    result = cur.fetchone()
    cur.close()
    conn.close()
    
    if result:
        role, user_id, deleted_at = result
        is_deleted = deleted_at is not None
        return role, user_id, is_deleted
    
    return None

def add_user(full_name, contact_info, email, password, role, start_date):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO users (
            full_name, contact_info, email, password, role, start_date
        ) VALUES (%s, %s, %s, %s, %s, %s)
    """, (full_name, contact_info, email, password, role, start_date))

    conn.commit()
    cur.close()
    conn.close()

