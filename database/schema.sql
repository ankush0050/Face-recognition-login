-- database/schema.sql
-- Face Recognition Employee Login System Database Schema

-- Drop tables if they exist (for clean setup)
DROP TABLE IF EXISTS login_logs;
DROP TABLE IF EXISTS face_encodings;
DROP TABLE IF EXISTS admin_users;
DROP TABLE IF EXISTS employees;

-- Create employees table
CREATE TABLE employees (
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
);

-- Create login_logs table
CREATE TABLE login_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT,
    login_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    confidence_score REAL,
    ip_address TEXT,
    user_agent TEXT,
    success BOOLEAN DEFAULT 1,
    failure_reason TEXT,
    FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
);

-- Create face_encodings table (for faster face matching)
CREATE TABLE face_encodings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT NOT NULL,
    encoding_data TEXT NOT NULL,  -- JSON array of face encoding
    encoding_hash TEXT NOT NULL,  -- Hash for quick comparison
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (employee_id) REFERENCES employees (employee_id)
);

-- Create admin_users table
CREATE TABLE admin_users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX idx_employees_employee_id ON employees(employee_id);
CREATE INDEX idx_employees_email ON employees(email);
CREATE INDEX idx_employees_is_active ON employees(is_active);
CREATE INDEX idx_login_logs_employee_id ON login_logs(employee_id);
CREATE INDEX idx_login_logs_login_time ON login_logs(login_time);
CREATE INDEX idx_face_encodings_employee_id ON face_encodings(employee_id);

-- Insert sample admin user (password: admin123)
INSERT INTO admin_users (username, password_hash, email) VALUES 
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeHdva4q0wKsyoqXy', 'admin@company.com');

-- Sample departments for reference
-- Engineering, Marketing, Sales, HR, Finance, Operations, IT, Other
