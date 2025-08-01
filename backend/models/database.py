import sqlite3
import json
import numpy as np
import os
from datetime import datetime
from typing import Optional, List, Tuple
import hashlib

class DatabaseManager:
    """Handles all database operations for the face recognition system"""
    
    def __init__(self, db_path: str = "face_recognition.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # This allows accessing columns by name
        return conn
    
    def init_database(self):
        """Initialize database with required tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Create employees table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                department TEXT,
                face_encoding TEXT,  -- JSON string of face encoding array
                photo_path TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create login_logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS login_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT,
                login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                confidence_score REAL,
                ip_address TEXT,
                user_agent TEXT,
                success BOOLEAN DEFAULT 1,
                failure_reason TEXT,
                FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
            )
        ''')
        
        # Create face_encodings table (for faster face matching)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS face_encodings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_id TEXT NOT NULL,
                encoding_data TEXT NOT NULL,  -- JSON array of face encoding
                encoding_hash TEXT NOT NULL,  -- Hash for quick comparison
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
            )
        ''')
        
        # Create admin_users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("✅ Database initialized successfully")
    
    def add_employee(self, employee_id: str, name: str, email: str, 
                    department: str, face_encoding: np.ndarray, 
                    photo_path: str = None) -> bool:
        """Add new employee with face encoding"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Convert numpy array to JSON string
            encoding_json = json.dumps(face_encoding.tolist())
            
            # Create hash of encoding for quick comparison
            encoding_hash = hashlib.md5(encoding_json.encode()).hexdigest()
            
            # Insert employee
            cursor.execute('''
                INSERT INTO employees 
                (employee_id, name, email, department, face_encoding, photo_path)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (employee_id, name, email, department, encoding_json, photo_path))
            
            # Insert face encoding for faster lookup
            cursor.execute('''
                INSERT INTO face_encodings 
                (employee_id, encoding_data, encoding_hash)
                VALUES (?, ?, ?)
            ''', (employee_id, encoding_json, encoding_hash))
            
            conn.commit()
            conn.close()
            print(f"✅ Employee {employee_id} added successfully")
            return True
            
        except sqlite3.IntegrityError as e:
            print(f"❌ Employee {employee_id} already exists: {e}")
            return False
        except Exception as e:
            print(f"❌ Error adding employee: {e}")
            return False
    
    def get_all_face_encodings(self) -> Tuple[List[np.ndarray], List[str]]:
        """Retrieve all face encodings and corresponding employee IDs"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT e.employee_id, fe.encoding_data 
            FROM employees e
            JOIN face_encodings fe ON e.employee_id = fe.employee_id
            WHERE e.is_active = 1
        ''')
        
        results = cursor.fetchall()
        conn.close()
        
        encodings = []
        employee_ids = []
        
        for row in results:
            try:
                # Convert JSON back to numpy array
                encoding = np.array(json.loads(row['encoding_data']))
                encodings.append(encoding)
                employee_ids.append(row['employee_id'])
            except Exception as e:
                print(f"⚠️ Error loading encoding for {row['employee_id']}: {e}")
                continue
        
        return encodings, employee_ids
    
    def get_employee_by_id(self, employee_id: str) -> Optional[dict]:
        """Get employee details by employee ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM employees WHERE employee_id = ? AND is_active = 1
        ''', (employee_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return dict(result)
        return None
    
    def log_login_attempt(self, employee_id: str = None, confidence: float = 0.0, 
                         success: bool = True, ip_address: str = None,
                         user_agent: str = None, failure_reason: str = None) -> bool:
        """Log login attempt"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO login_logs 
                (employee_id, confidence_score, success, ip_address, user_agent, failure_reason)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (employee_id, confidence, success, ip_address, user_agent, failure_reason))
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error logging login attempt: {e}")
            return False
    
    def get_login_history(self, employee_id: str = None, limit: int = 50) -> List[dict]:
        """Get login history for an employee or all employees"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if employee_id:
            cursor.execute('''
                SELECT ll.*, e.name 
                FROM login_logs ll
                LEFT JOIN employees e ON ll.employee_id = e.employee_id
                WHERE ll.employee_id = ?
                ORDER BY ll.login_time DESC
                LIMIT ?
            ''', (employee_id, limit))
        else:
            cursor.execute('''
                SELECT ll.*, e.name 
                FROM login_logs ll
                LEFT JOIN employees e ON ll.employee_id = e.employee_id
                ORDER BY ll.login_time DESC
                LIMIT ?
            ''', (limit,))
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
    
    def update_employee(self, employee_id: str, **kwargs) -> bool:
        """Update employee information"""
        try:
            conn = self.get_connection()
            cursor = conn.cursor()
            
            # Build dynamic update query
            update_fields = []
            values = []
            
            for key, value in kwargs.items():
                if key in ['name', 'email', 'department', 'is_active']:
                    update_fields.append(f"{key} = ?")
                    values.append(value)
            
            if not update_fields:
                return False
            
            # Add updated_at timestamp
            update_fields.append("updated_at = ?")
            values.append(datetime.now())
            values.append(employee_id)
            
            query = f"UPDATE employees SET {', '.join(update_fields)} WHERE employee_id = ?"
            cursor.execute(query, values)
            
            conn.commit()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error updating employee: {e}")
            return False
    
    def delete_employee(self, employee_id: str) -> bool:
        """Soft delete employee (set is_active to False)"""
        return self.update_employee(employee_id, is_active=False)
    
    def get_all_employees(self, active_only: bool = True) -> List[dict]:
        """Get all employees"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        if active_only:
            cursor.execute("SELECT * FROM employees WHERE is_active = 1 ORDER BY name")
        else:
            cursor.execute("SELECT * FROM employees ORDER BY name")
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
    
    def search_employees(self, query: str) -> List[dict]:
        """Search employees by name, email, or employee_id"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        search_pattern = f"%{query}%"
        cursor.execute('''
            SELECT * FROM employees 
            WHERE (name LIKE ? OR email LIKE ? OR employee_id LIKE ?)
            AND is_active = 1
            ORDER BY name
        ''', (search_pattern, search_pattern, search_pattern))
        
        results = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in results]
    
    def get_stats(self) -> dict:
        """Get system statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Total active employees
        cursor.execute("SELECT COUNT(*) as total FROM employees WHERE is_active = 1")
        total_employees = cursor.fetchone()['total']
        
        # Total logins today
        cursor.execute('''
            SELECT COUNT(*) as today_logins 
            FROM login_logs 
            WHERE DATE(login_time) = DATE('now') AND success = 1
        ''')
        today_logins = cursor.fetchone()['today_logins']
        
        # Failed attempts today
        cursor.execute('''
            SELECT COUNT(*) as failed_attempts 
            FROM login_logs 
            WHERE DATE(login_time) = DATE('now') AND success = 0
        ''')
        failed_attempts = cursor.fetchone()['failed_attempts']
        
        # Most recent login
        cursor.execute('''
            SELECT ll.login_time, e.name 
            FROM login_logs ll
            JOIN employees e ON ll.employee_id = e.employee_id
            WHERE ll.success = 1
            ORDER BY ll.login_time DESC
            LIMIT 1
        ''')
        recent_login = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_employees': total_employees,
            'today_logins': today_logins,
            'failed_attempts': failed_attempts,
            'recent_login': dict(recent_login) if recent_login else None
        }
    
    def close(self):
        """Close database connection (cleanup method)"""
        pass  # SQLite connections are closed after each operation

# Initialize database when module is imported
if __name__ == "__main__":
    # Test the database
    db = DatabaseManager()
    print("Database setup complete!")
    
    # Print stats
    stats = db.get_stats()
    print(f"System Stats: {stats}")