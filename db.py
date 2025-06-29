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
        'xp': 'INTEGER DEFAULT 0',
        'level': 'INTEGER DEFAULT 1',
        'credits': 'INTEGER DEFAULT 0',
        'pets': 'TEXT',
        'inventory': 'TEXT',
        'equipped_weapon': 'VARCHAR(100)',
        'last_daily': 'TIMESTAMP',
        'last_weekly': 'TIMESTAMP',
        'achievements': 'TEXT',
        'pet_stats': 'TEXT',
        'pet_last_train': 'TEXT',
        'mission_progress': 'TEXT',
        'quiz_last': 'TIMESTAMP',
        'team': 'VARCHAR(100)',
        'team_role': 'VARCHAR(50)',
        'team_points': 'INTEGER DEFAULT 0',
        'last_mission_start': 'TIMESTAMP',
        'equipped_pets': 'TEXT DEFAULT \'[]\'',
        'battle_team': 'TEXT DEFAULT \'[]\'',
        'damaged_items': 'TEXT',
        'equipped_gun': 'VARCHAR(255)',
        'daily_streak': 'INTEGER DEFAULT 0',
        'weekly_streak': 'INTEGER DEFAULT 0',
        'inventory_value': 'INTEGER DEFAULT 0',
        'created_at': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
    },
    'teams': {
        'name': 'VARCHAR(100) PRIMARY KEY',
        'owner': 'BIGINT',
        'members': 'TEXT',
        'created': 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP',
        'points': 'INTEGER DEFAULT 0',
        'icon': 'TEXT',
        'description': 'TEXT',
        'achievements': 'TEXT',
        'quest': 'TEXT'
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
    
    # Run migrations to add missing columns
    migrate_tables(cursor)
    
    conn.commit()
    cursor.close()
    conn.close()

def migrate_tables(cursor):
    """Add missing columns to existing tables"""
    try:
        # Check if equipped_pets column exists in users table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'equipped_pets'
        """)
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE users ADD COLUMN equipped_pets TEXT DEFAULT '[]'")
            print("Added equipped_pets column to users table")
        
        # Check if battle_team column exists in users table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'battle_team'
        """)
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE users ADD COLUMN battle_team TEXT DEFAULT '[]'")
            print("Added battle_team column to users table")
        
        # Check if damaged_items column exists in users table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'damaged_items'
        """)
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE users ADD COLUMN damaged_items TEXT DEFAULT '[]'")
            print("Added damaged_items column to users table")
        
        # Check if equipped_gun column exists in users table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'equipped_gun'
        """)
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE users ADD COLUMN equipped_gun VARCHAR(255)")
            print("Added equipped_gun column to users table")
        
        # Check if daily_streak column exists in users table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'daily_streak'
        """)
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE users ADD COLUMN daily_streak INTEGER DEFAULT 0")
            print("Added daily_streak column to users table")
        
        # Check if weekly_streak column exists in users table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'weekly_streak'
        """)
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE users ADD COLUMN weekly_streak INTEGER DEFAULT 0")
            print("Added weekly_streak column to users table")
        
        # Check if inventory_value column exists in users table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'inventory_value'
        """)
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE users ADD COLUMN inventory_value INTEGER DEFAULT 0")
            print("Added inventory_value column to users table")
        
        # Check if created_at column exists in users table
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'created_at'
        """)
        if not cursor.fetchone():
            cursor.execute("ALTER TABLE users ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
            print("Added created_at column to users table")
            
    except Exception as e:
        print(f"Error during migration: {e}")

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

# --- INVENTORY VALUE HELPERS ---
def calculate_inventory_value(inventory_items):
    """Calculate the total value of inventory items"""
    # Item prices (you can adjust these)
    item_prices = {
        # Weapons
        "Pistol": 1000,
        "SMG": 2500,
        "Rifle": 5000,
        "Sniper": 10000,
        "Shotgun": 3000,
        "LMG": 8000,
        
        # Keycards
        "Keycard Level 1": 500,
        "Keycard Level 2": 1000,
        "Keycard Level 3": 2000,
        "Keycard Level 4": 5000,
        "Keycard Level 5": 10000,
        
        # Containment items
        "Containment Suit": 1500,
        "SCP Plushie": 100,
        "SCP-999 Plushie": 200,
        "SCP-682 Plushie": 500,
        
        # Other items
        "Medkit": 300,
        "Flashlight": 50,
        "Radio": 200,
        "Gas Mask": 400,
        "Bulletproof Vest": 800,
        
        # Default price for unknown items
        "default": 100
    }
    
    total_value = 0
    for item in inventory_items:
        item_value = item_prices.get(item, item_prices["default"])
        total_value += item_value
    
    return total_value

def update_inventory_value(user_id):
    """Update the inventory_value field for a user based on their current inventory"""
    user = get_user(user_id)
    inventory_value = calculate_inventory_value(user.get('inventory', []))
    update_user(user_id, inventory_value=inventory_value)
    return inventory_value

# --- USER HELPERS ---
def get_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    if not user:
        # Create new user if not found - use a simpler INSERT that only includes basic fields
        try:
            cursor.execute(
                """INSERT INTO users (id, xp, level, credits, pets, inventory) 
                VALUES (%s, %s, %s, %s, %s, %s)""",
                (user_id, 0, 1, 0, '[]', '[]')
            )
            conn.commit()
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
        except Exception as e:
            print(f"Error creating user: {e}")
            # If INSERT fails, try to create with minimal fields
            cursor.execute(
                """INSERT INTO users (id) VALUES (%s)""",
                (user_id,)
            )
            conn.commit()
            cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
            user = cursor.fetchone()
    
    # Convert TEXT fields that contain JSON data to Python objects
    json_fields = ['pets', 'inventory', 'achievements', 'pet_stats', 'pet_last_train', 'mission_progress', 'damaged_items', 'equipped_pets', 'battle_team']
    for field in json_fields:
        if field in user and user[field]:
            try:
                user[field] = json.loads(user[field]) if isinstance(user[field], str) else user[field]
            except json.JSONDecodeError:
                # If it's not valid JSON, treat as empty
                user[field] = [] if field in ['pets', 'inventory', 'achievements', 'damaged_items', 'equipped_pets', 'battle_team'] else {}
        else:
            user[field] = [] if field in ['pets', 'inventory', 'achievements', 'damaged_items', 'equipped_pets', 'battle_team'] else {}
    
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
        # Parse TEXT fields that contain JSON data
        for field in ['members', 'achievements', 'quest']:
            if team[field]:
                try:
                    team[field] = json.loads(team[field]) if isinstance(team[field], str) else team[field]
                except json.JSONDecodeError:
                    # If it's not valid JSON, treat as empty
                    team[field] = [] if field in ['members', 'achievements'] else {}
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
        # Parse TEXT fields that contain JSON data
        for field in ['members', 'achievements', 'quest']:
            if team[field]:
                try:
                    team[field] = json.loads(team[field]) if isinstance(team[field], str) else team[field]
                except json.JSONDecodeError:
                    # If it's not valid JSON, treat as empty
                    team[field] = [] if field in ['members', 'achievements'] else {}
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
        # Convert TEXT fields that contain JSON data to Python objects
        json_fields = ['pets', 'inventory', 'achievements', 'pet_stats', 'pet_last_train', 'mission_progress', 'damaged_items', 'equipped_pets', 'battle_team']
        for field in json_fields:
            if field in user and user[field]:
                try:
                    user[field] = json.loads(user[field]) if isinstance(user[field], str) else user[field]
                except json.JSONDecodeError:
                    # If it's not valid JSON, treat as empty
                    user[field] = [] if field in ['pets', 'inventory', 'achievements', 'damaged_items', 'equipped_pets', 'battle_team'] else {}
            else:
                user[field] = [] if field in ['pets', 'inventory', 'achievements', 'damaged_items', 'equipped_pets', 'battle_team'] else {}
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