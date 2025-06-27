def authenticate_user(email, password):
    from db4 import get_connection
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT role, user_id FROM users WHERE email = %s AND password = %s", (email, password))
    result = cur.fetchone()
    cur.close()
    conn.close()
    if result:
        return result[0], result[1]  # role, user_id
    return None