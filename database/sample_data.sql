-- database/sample_data.sql
-- Sample data for testing the Face Recognition Employee Login System

-- Insert sample employees (without face encodings for now)
INSERT INTO employees (employee_id, name, email, department, is_active) VALUES 
('EMP001', 'John Doe', 'john.doe@company.com', 'Engineering', 1),
('EMP002', 'Jane Smith', 'jane.smith@company.com', 'Marketing', 1),
('EMP003', 'Mike Johnson', 'mike.johnson@company.com', 'Sales', 1),
('EMP004', 'Sarah Wilson', 'sarah.wilson@company.com', 'HR', 1),
('EMP005', 'David Brown', 'david.brown@company.com', 'Finance', 1);

-- Insert sample login logs (for demonstration)
INSERT INTO login_logs (employee_id, confidence_score, success, ip_address) VALUES 
('EMP001', 0.95, 1, '192.168.1.100'),
('EMP002', 0.88, 1, '192.168.1.101'),
('EMP001', 0.92, 1, '192.168.1.100'),
('EMP003', 0.45, 0, '192.168.1.102'),
('EMP004', 0.89, 1, '192.168.1.103');
