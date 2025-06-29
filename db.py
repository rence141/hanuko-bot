# db.py
import psycopg2
import psycopg2.extras
import json
import os

# Try to import config, fall back to config_fallback if not available
try:
    import config
    db_config = config.DB_CONFIG
except ImportError:
    import config_fallback as config
    db_config = config.DB_CONFIG

# Database Schema Definition - Your bot knows about tables and columns here
SCHEMA = {
    'users': {
        'id': 'BIGINT PRIMARY KEY',
        'pets': 'JSONB DEFAULT \'[]\'',
        'inventory': 'JSONB DEFAULT \'[]\'',
        'achievements': 'JSONB DEFAULT \'[]\'',
        'pet_stats': 'JSONB DEFAULT \'{}\'',
        'pet_last_train': 'JSONB DEFAULT \'{}\'',
        'mission_progress': 'JSONB DEFAULT \'{}\'',
        'credits': 'INTEGER DEFAULT 0',
        'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
    },
    'teams': {
        'name': 'VARCHAR(255) PRIMARY KEY',
        'members': 'JSONB DEFAULT \'[]\'',
        'achievements': 'JSONB DEFAULT \'[]\'',
        'quest': 'JSONB DEFAULT \'{}\'',
        'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
    },
    'polls': {
        'id': 'SERIAL PRIMARY KEY',
        'question': 'TEXT NOT NULL',
        'options': 'JSONB NOT NULL',
        'votes': 'JSONB DEFAULT \'{}\'',
        'created_by': 'BIGINT NOT NULL',
        'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
    },
    'warnings': {
        'id': 'SERIAL PRIMARY KEY',
        'user_id': 'BIGINT NOT NULL',
        'reason': 'TEXT NOT NULL',
        'moderator_id': 'BIGINT NOT NULL',
        'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
    }
}

def get_db_connection():
    return psycopg2.connect(**db_config)

def create_tables():
    """Create all tables if they don't exist - your bot knows the structure here"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for table_name, columns in SCHEMA.items():
        # Build CREATE TABLE statement
        column_definitions = []
        for col_name, col_type in columns.items():
            column_definitions.append(f"{col_name} {col_type}")
        
        create_sql = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {', '.join(column_definitions)}
        );
        """
        
        try:
            cursor.execute(create_sql)
            print(f"Table {table_name} created/verified successfully")
        except Exception as e:
            print(f"Error creating table {table_name}: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()

def get_table_structure(table_name):
    """Get the actual structure of a table from the database"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    sql = """
    SELECT column_name, data_type, is_nullable, column_default
    FROM information_schema.columns 
    WHERE table_name = %s
    ORDER BY ordinal_position;
    """
    
    cursor.execute(sql, (table_name,))
    columns = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return columns

# --- USER HELPERS ---
def get_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
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
            user[field] = json.loads(user[field]) if isinstance(user[field], str) else user[field]
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
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM teams WHERE name = %s", (team_name,))
    team = cursor.fetchone()
    if team:
        for field in ['members', 'achievements', 'quest']:
            if team[field]:
                team[field] = json.loads(team[field]) if isinstance(team[field], str) else team[field]
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

# --- ADMIN HELPERS ---
def get_all_teams():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM teams")
    teams = cursor.fetchall()
    for team in teams:
        for field in ['members', 'achievements', 'quest']:
            if team[field]:
                team[field] = json.loads(team[field]) if isinstance(team[field], str) else team[field]
            else:
                team[field] = [] if field in ['members', 'achievements'] else {}
    cursor.close()
    conn.close()
    return teams

def get_all_users():
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    for user in users:
        for field in ['pets', 'inventory', 'achievements', 'pet_stats', 'pet_last_train', 'mission_progress']:
            if user[field]:
                user[field] = json.loads(user[field]) if isinstance(user[field], str) else user[field]
            else:
                user[field] = [] if field in ['pets', 'inventory', 'achievements'] else {}
    cursor.close()
    conn.close()
    return users

# Initialize database tables when module is imported
if __name__ == "__main__":
    create_tables()

# Example user/team data helpers (implement as needed)
# def get_user(user_id): ...
# def update_user(user_id, ...): ...
# def get_team(team_name): ...
# def update_team(team_name, ...): ... 