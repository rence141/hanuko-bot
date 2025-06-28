# db.py
import mysql.connector
import json

# MySQL connection settings (edit as needed)
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '003421.!',
    'database': 'Hanuko'
}

def get_db_connection():
    return mysql.connector.connect(**db_config)

# --- USER HELPERS ---
def get_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if not user:
        # Create new user if not found
        cursor.execute(
            "INSERT INTO users (id, pets, inventory, achievements, pet_stats, pet_last_train, mission_progress) VALUES (%s, %s, %s, %s, %s, %s, %s)",
            (user_id, '[]', '[]', '[]', '{}', '{}', '{}')
        )
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        user = cursor.fetchone()
    # Convert JSON fields to Python objects
    for field in ['pets', 'inventory', 'achievements', 'pet_stats', 'pet_last_train', 'mission_progress']:
        if user[field]:
            user[field] = json.loads(user[field])
        else:
            user[field] = [] if field in ['pets', 'inventory', 'achievements'] else {}
    cursor.close()
    conn.close()
    return user

def update_user(user_id, **kwargs):
    conn = get_db_connection()
    cursor = conn.cursor()
    fields = []
    values = []
    for k, v in kwargs.items():
        if isinstance(v, (list, dict)):
            v = json.dumps(v)
        fields.append(f"{k} = %s")
        values.append(v)
    values.append(user_id)
    sql = f"UPDATE users SET {', '.join(fields)} WHERE id = %s"
    cursor.execute(sql, values)
    conn.commit()
    cursor.close()
    conn.close()

# --- TEAM HELPERS ---
def get_team(team_name):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM teams WHERE name = %s", (team_name,))
    team = cursor.fetchone()
    if team:
        for field in ['members', 'achievements', 'quest']:
            if team[field]:
                team[field] = json.loads(team[field])
            else:
                team[field] = [] if field in ['members', 'achievements'] else {}
    cursor.close()
    conn.close()
    return team

def update_team(team_name, **kwargs):
    conn = get_db_connection()
    cursor = conn.cursor()
    fields = []
    values = []
    for k, v in kwargs.items():
        if isinstance(v, (list, dict)):
            v = json.dumps(v)
        fields.append(f"{k} = %s")
        values.append(v)
    values.append(team_name)
    sql = f"UPDATE teams SET {', '.join(fields)} WHERE name = %s"
    cursor.execute(sql, values)
    conn.commit()
    cursor.close()
    conn.close()

# --- OPTIONAL: Get all teams/users (for stats/admin) ---
def get_all_teams():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM teams")
    teams = cursor.fetchall()
    for team in teams:
        for field in ['members', 'achievements', 'quest']:
            if team[field]:
                team[field] = json.loads(team[field])
            else:
                team[field] = [] if field in ['members', 'achievements'] else {}
    cursor.close()
    conn.close()
    return teams

def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    for user in users:
        for field in ['pets', 'inventory', 'achievements', 'pet_stats', 'pet_last_train', 'mission_progress']:
            if user[field]:
                user[field] = json.loads(user[field])
            else:
                user[field] = [] if field in ['pets', 'inventory', 'achievements'] else {}
    cursor.close()
    conn.close()
    return users

# Example user/team data helpers (implement as needed)
# def get_user(user_id): ...
# def update_user(user_id, ...): ...
# def get_team(team_name): ...
# def update_team(team_name, ...): ... 