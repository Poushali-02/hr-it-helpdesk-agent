INSERT INTO employees (employee_id, name, department, role, manager_id, work_email, phone, personal_email, pan) VALUES
('E001', 'Meera Iyer',     'HR',          'HR Manager',          NULL,   'meera.iyer@northwind.example',   '+91 98100 10001', 'meera.iyer@gmail.com',   'ABCPI1001A'),
('E101', 'Rohan Mehta',    'Engineering', 'Engineering Manager', 'E001', 'rohan.mehta@northwind.example',  '+91 98100 10101', 'rohan.mehta@gmail.com',  'ABCPM1101B'),
('E102', 'Priya Nair',     'Engineering', 'Software Engineer',   'E101', 'priya.nair@northwind.example',   '+91 98100 10102', 'priya.nair22@gmail.com', 'BQRPN4102C'),
('E103', 'Arjun Das',      'Engineering', 'Software Engineer',   'E101', 'arjun.das@northwind.example',    '+91 98100 10103', 'arjun.das@outlook.com',  'CDEPD7103D'),
('E104', 'Sana Khan',      'Design',      'Product Designer',    'E001', 'sana.khan@northwind.example',    '+91 98100 10104', 'sana.khan@gmail.com',    'DEFPK2104E'),
('E105', 'Vikram Singh',   'Sales',       'Account Executive',   'E001', 'vikram.singh@northwind.example', '+91 98100 10105', 'vikram.s@gmail.com',     'EFGPS5105F'),
('E106', 'Ananya Rao',     'Finance',     'Accountant',          'E001', 'ananya.rao@northwind.example',   '+91 98100 10106', 'ananya.rao@gmail.com',   'FGHPR8106G'),
('E107', 'Karan Joshi',    'Engineering', 'QA Engineer',         'E101', 'karan.joshi@northwind.example',  '+91 98100 10107', 'karan.j@gmail.com',      'GHIPJ3107H'),
('E108', 'Neha Gupta',     'Support',     'Support Lead',        'E001', 'neha.gupta@northwind.example',   '+91 98100 10108', 'neha.gupta@gmail.com',   'HIJPG6108J'),
('E109', 'Dev Patel',      'Engineering', 'DevOps Engineer',     'E101', 'dev.patel@northwind.example',    '+91 98100 10109', 'dev.patel@gmail.com',    'IJKPP9109K'),
('E110', 'Ishita Bose',    'Marketing',   'Marketing Associate', 'E001', 'ishita.bose@northwind.example',  '+91 98100 10110', 'ishita.bose@gmail.com',  'JKLPB1110L');

INSERT INTO leave_balances (employee_id, leave_type, entitled, used)
SELECT e.employee_id, t.leave_type, t.entitled,
       CASE WHEN e.employee_id = 'E102' THEN
                 CASE t.leave_type WHEN 'casual' THEN 4 WHEN 'sick' THEN 2 ELSE 6 END
            ELSE (substring(e.employee_id from 2)::int % 4) END
FROM employees e
CROSS JOIN (VALUES ('casual', 12), ('sick', 10), ('earned', 15)) AS t(leave_type, entitled);
