import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'smart_building.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # ตาราง อาคาร
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS buildings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            floors INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # ตาราง ห้อง/พื้นที่
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rooms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            building_id INTEGER NOT NULL,
            room_number TEXT NOT NULL,
            floor INTEGER,
            room_type TEXT,
            area_sqm REAL,
            FOREIGN KEY (building_id) REFERENCES buildings(id)
        )
    ''')

    # ตาราง เจ้าของ/ผู้เช่า
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS owners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            owner_type TEXT DEFAULT 'เจ้าของ',
            move_in_date DATE,
            note TEXT,
            FOREIGN KEY (room_id) REFERENCES rooms(id)
        )
    ''')

    # ตาราง อุปกรณ์
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            equipment_type TEXT,
            brand TEXT,
            model TEXT,
            serial_number TEXT UNIQUE,
            install_date DATE,
            warranty_expire DATE,
            status TEXT DEFAULT 'ปกติ',
            FOREIGN KEY (room_id) REFERENCES rooms(id)
        )
    ''')

    # ตาราง ช่างเทคนิค
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS technicians (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            specialization TEXT,
            available INTEGER DEFAULT 1
        )
    ''')

    # ตาราง บันทึกซ่อมบำรุง (ตารางหลัก)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS maintenance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_id INTEGER NOT NULL,
            technician_id INTEGER,
            report_date DATE NOT NULL,
            issue_description TEXT NOT NULL,
            action_taken TEXT,
            cost REAL DEFAULT 0,
            status TEXT DEFAULT 'รอดำเนินการ',
            priority TEXT DEFAULT 'ปกติ',
            completed_date DATE,
            FOREIGN KEY (equipment_id) REFERENCES equipment(id),
            FOREIGN KEY (technician_id) REFERENCES technicians(id)
        )
    ''')

    # เพิ่มข้อมูล Mock
    cursor.execute("SELECT COUNT(*) FROM buildings")
    if cursor.fetchone()[0] == 0:
        _insert_mock_data(cursor)

    conn.commit()
    conn.close()
    print("Database initialized successfully!")

def _insert_mock_data(cursor):
    # อาคาร (3 records)
    buildings = [
        ('อาคาร A', 'ชั้น 1-5 โซนเหนือ', 5),
        ('อาคาร B', 'ชั้น 1-3 โซนใต้', 3),
        ('อาคาร C', 'ชั้น 1-4 โซนตะวันออก', 4),
    ]
    cursor.executemany("INSERT INTO buildings (name, address, floors) VALUES (?,?,?)", buildings)

    # ห้อง (12 records)
    rooms = [
        (1, '101', 1, 'สำนักงาน', 45.0),
        (1, '102', 1, 'ห้องประชุม', 30.0),
        (1, '201', 2, 'สำนักงาน', 50.0),
        (1, '301', 3, 'ห้องเซิร์ฟเวอร์', 20.0),
        (1, '401', 4, 'ห้องฝึกอบรม', 60.0),
        (2, 'B101', 1, 'ล็อบบี้', 80.0),
        (2, 'B102', 1, 'ห้องน้ำ', 15.0),
        (1, '202', 2, 'ห้องพัก', 25.0),
        (2, 'B201', 2, 'สำนักงาน', 40.0),
        (3, 'C101', 1, 'ห้องรับแขก', 35.0),
        (3, 'C201', 2, 'ห้องประชุมใหญ่', 70.0),
        (3, 'C301', 3, 'สำนักงาน', 55.0),
    ]
    cursor.executemany("INSERT INTO rooms (building_id, room_number, floor, room_type, area_sqm) VALUES (?,?,?,?,?)", rooms)

    # อุปกรณ์ (15 records)
    equipment = [
        (1,  'เครื่องปรับอากาศ',   'แอร์',          'Daikin',    'FTKM35',         'SN001', '2022-01-15', '2025-01-15', 'ปกติ'),
        (1,  'ไฟส่องสว่าง LED',    'ไฟ',            'Philips',   'CorePro',         'SN002', '2022-01-15', '2024-01-15', 'ปกติ'),
        (2,  'โปรเจกเตอร์',        'อุปกรณ์AV',     'Epson',     'EB-X41',          'SN003', '2021-06-01', '2024-06-01', 'ชำรุด'),
        (3,  'เครื่องปรับอากาศ',   'แอร์',          'Mitsubishi','MSZ-GE25',        'SN004', '2020-03-10', '2023-03-10', 'ปกติ'),
        (4,  'UPS',                 'ไฟฟ้า',         'APC',       'BR1500G',         'SN005', '2021-11-20', '2024-11-20', 'ปกติ'),
        (4,  'เซิร์ฟเวอร์',        'IT',            'Dell',      'PowerEdge R440',  'SN006', '2021-11-20', '2024-11-20', 'ปกติ'),
        (6,  'ลิฟต์',              'ลิฟต์',         'Otis',      'Gen2',            'SN007', '2019-05-01', '2024-05-01', 'ซ่อมอยู่'),
        (7,  'ปั๊มน้ำ',            'ระบบน้ำ',       'Grundfos',  'CM5-6',           'SN008', '2020-08-15', '2023-08-15', 'ปกติ'),
        (8,  'เครื่องปรับอากาศ',   'แอร์',          'Samsung',   'AR18TYHD',        'SN009', '2023-02-01', '2026-02-01', 'ปกติ'),
        (9,  'กล้องวงจรปิด',       'ความปลอดภัย',   'Hikvision', 'DS-2CD2143G2',    'SN010', '2022-07-10', '2025-07-10', 'ปกติ'),
        (5,  'โปรเจกเตอร์',        'อุปกรณ์AV',     'BenQ',      'MX726',           'SN011', '2022-09-01', '2025-09-01', 'ปกติ'),
        (10, 'เครื่องปรับอากาศ',   'แอร์',          'LG',        'S18EQ',           'SN012', '2023-03-15', '2026-03-15', 'ปกติ'),
        (11, 'ระบบเสียง',          'อุปกรณ์AV',     'Bose',      'FreeSpace 3',     'SN013', '2021-04-20', '2024-04-20', 'ชำรุด'),
        (12, 'สวิตช์เครือข่าย',   'IT',            'Cisco',     'SG350-28',        'SN014', '2020-12-01', '2023-12-01', 'ปกติ'),
        (3,  'กล้องวงจรปิด',       'ความปลอดภัย',   'Dahua',     'IPC-HDW2831T',    'SN015', '2023-06-10', '2026-06-10', 'ปกติ'),
    ]
    cursor.executemany("""INSERT INTO equipment 
        (room_id, name, equipment_type, brand, model, serial_number, install_date, warranty_expire, status) 
        VALUES (?,?,?,?,?,?,?,?,?)""", equipment)

    # ช่างเทคนิค (7 records)
    technicians = [
        ('สมชาย ใจดี',      '081-111-1111', 'ระบบไฟฟ้า',    1),
        ('วิชัย แข็งแกร่ง', '082-222-2222', 'ระบบแอร์',     1),
        ('ประสิทธิ์ มือทอง', '083-333-3333', 'ระบบน้ำ',      1),
        ('นภา สายฝน',       '084-444-4444', 'IT/เครือข่าย', 1),
        ('อนุชา ช่างเก่ง',  '085-555-5555', 'งานทั่วไป',    0),
        ('ธนกร วิชาช่าง',   '086-666-6666', 'ระบบความปลอดภัย', 1),
        ('มานะ ตั้งใจ',     '087-777-7777', 'อุปกรณ์AV',    1),
    ]
    cursor.executemany("INSERT INTO technicians (name, phone, specialization, available) VALUES (?,?,?,?)", technicians)

    # บันทึกซ่อมบำรุง (20 records)
    logs = [
        (3,  2, '2024-01-10', 'โปรเจกเตอร์ภาพไม่ชัด หลอดแสงหรี่',        'เปลี่ยนหลอด',                    2500, 'เสร็จสิ้น',        'ปกติ',   '2024-01-12'),
        (7,  1, '2024-02-15', 'ลิฟต์กระตุก มีเสียงดัง',                   'กำลังตรวจสอบ',                   0,    'กำลังดำเนินการ',   'ด่วน',   None),
        (1,  2, '2024-03-01', 'แอร์ไม่เย็น น้ำแข็งเกาะ',                  'ล้างแอร์ เติมน้ำยา',             800,  'เสร็จสิ้น',        'ปกติ',   '2024-03-02'),
        (5,  4, '2024-03-10', 'UPS แจ้งเตือน battery ต่ำ',                 'เปลี่ยนแบตเตอรี่',               4500, 'เสร็จสิ้น',        'ด่วน',   '2024-03-11'),
        (8,  3, '2024-04-05', 'ปั๊มน้ำมีเสียงดัง แรงดันตก',               'รอตรวจสอบ',                      0,    'รอดำเนินการ',      'ปกติ',   None),
        (2,  1, '2024-04-20', 'หลอดไฟดับ 3 ดวง',                           'เปลี่ยนหลอดใหม่',                300,  'เสร็จสิ้น',        'ปกติ',   '2024-04-20'),
        (10, 6, '2024-05-01', 'กล้องวงจรปิดภาพพร่ามัว',                   'ปรับโฟกัส ทำความสะอาดเลนส์',    200,  'เสร็จสิ้น',        'ปกติ',   '2024-05-01'),
        (4,  2, '2024-05-15', 'แอร์ในห้องประชุมรั่ว',                      'รอช่าง',                         0,    'รอดำเนินการ',      'ด่วน',   None),
        (9,  2, '2024-06-01', 'ตรวจสภาพประจำปี',                           'ล้างแอร์ ตรวจระบบ',              600,  'เสร็จสิ้น',        'ปกติ',   '2024-06-01'),
        (6,  4, '2024-06-10', 'เซิร์ฟเวอร์ร้อนผิดปกติ พัดลมดัง',         'เปลี่ยนพัดลม ทำความสะอาด',      1200, 'เสร็จสิ้น',        'ด่วนมาก','2024-06-10'),
        (1,  2, '2024-07-01', 'แอร์ไม่ทำงาน',                              'ตรวจสอบระบบไฟ เปลี่ยนฟิวส์',    350,  'เสร็จสิ้น',        'ปกติ',   '2024-07-03'),
        (3,  7, '2024-07-15', 'โปรเจกเตอร์ไม่ติด',                        'เช็คสายไฟ เปลี่ยนสายHDMI',       150,  'เสร็จสิ้น',        'ปกติ',   '2024-07-15'),
        (13, 7, '2024-08-01', 'ระบบเสียงห้องประชุมใหญ่ดังแผ่ว',           'ปรับค่า Amplifier',               0,    'กำลังดำเนินการ',   'ปกติ',   None),
        (14, 4, '2024-08-10', 'สวิตช์เครือข่ายพอร์ตเสีย 2 พอร์ต',        'เปลี่ยนสวิตช์ใหม่',              3800, 'เสร็จสิ้น',        'ด่วน',   '2024-08-12'),
        (11, 2, '2024-08-20', 'แอร์อาคาร C รั่วน้ำ',                      'อุดรอยรั่ว เติมน้ำยา',           900,  'เสร็จสิ้น',        'ด่วน',   '2024-08-21'),
        (12, 3, '2024-09-05', 'ท่อน้ำห้องน้ำอาคาร B รั่ว',                'เปลี่ยนท่อ ซ่อมวาล์ว',          1500, 'เสร็จสิ้น',        'ด่วนมาก','2024-09-05'),
        (15, 6, '2024-09-15', 'กล้องวงจรปิดห้องประชุมออฟไลน์',            'ตรวจสอบสาย ตั้งค่าใหม่',         0,    'เสร็จสิ้น',        'ปกติ',   '2024-09-16'),
        (5,  4, '2024-10-01', 'UPS เตือน overload',                        'ตรวจสอบ load ลดการใช้ไฟ',        0,    'รอดำเนินการ',      'ด่วน',   None),
        (2,  1, '2024-10-10', 'ไฟทางเดินชั้น 1 กะพริบ',                   'เปลี่ยน ballast หลอดไฟ',         450,  'เสร็จสิ้น',        'ปกติ',   '2024-10-11'),
        (7,  1, '2024-10-20', 'ลิฟต์หยุดกลางคัน ประตูไม่ปิด',            'ซ่อมระบบประตู ปรับ sensor',      5500, 'เสร็จสิ้น',        'ด่วนมาก','2024-10-22'),
    ]
    cursor.executemany("""INSERT INTO maintenance_logs 
        (equipment_id, technician_id, report_date, issue_description, action_taken, cost, status, priority, completed_date) 
        VALUES (?,?,?,?,?,?,?,?,?)""", logs)

if __name__ == '__main__':
    init_db()

def add_owners_table():
    """เรียกครั้งเดียวเพื่อเพิ่มตาราง owners ในฐานข้อมูลที่มีอยู่แล้ว"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS owners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            room_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            phone TEXT,
            email TEXT,
            owner_type TEXT DEFAULT 'เจ้าของ',
            move_in_date DATE,
            note TEXT,
            FOREIGN KEY (room_id) REFERENCES rooms(id)
        )
    ''')
    cursor.execute("SELECT COUNT(*) FROM owners")
    if cursor.fetchone()[0] == 0:
        owners = [
            (1,  'บริษัท เอ็กซ์เซล จำกัด',       '02-111-1111',  'excel@mail.com',   'ผู้เช่า',  '2022-01-01', 'สัญญา 3 ปี'),
            (2,  'ฝ่ายบริหาร อาคาร A',            '02-111-2222',  'admin@mail.com',   'เจ้าของ',  '2020-06-01', 'ห้องประชุมกลาง'),
            (3,  'บริษัท ดิจิทัล โซลูชัน จำกัด',  '02-222-1111',  'digital@mail.com', 'ผู้เช่า',  '2021-03-15', 'สัญญา 2 ปี'),
            (4,  'ฝ่าย IT อาคาร A',               '02-111-3333',  'it@mail.com',      'เจ้าของ',  '2019-01-01', 'ห้องเซิร์ฟเวอร์หลัก'),
            (5,  'บริษัท ครีเอทีฟ จำกัด',         '02-333-1111',  'creative@mail.com','ผู้เช่า',  '2023-01-10', 'สัญญา 1 ปี'),
            (6,  'นายสมศักดิ์ รักดี',             '081-100-1111', 'somsak@mail.com',  'เจ้าของ',  '2018-05-01', None),
            (7,  'ห้องน้ำส่วนกลาง อาคาร B',       '02-444-0000',  None,               'เจ้าของ',  '2018-05-01', 'พื้นที่ส่วนกลาง'),
            (8,  'นางสาวมาลี สวยงาม',             '082-200-2222', 'malee@mail.com',   'ผู้เช่า',  '2022-07-01', 'สัญญา 2 ปี'),
            (9,  'บริษัท โกลบอล เทรด จำกัด',      '02-555-1111',  'global@mail.com',  'ผู้เช่า',  '2023-04-01', 'สัญญา 1 ปี'),
            (10, 'นายวิรัตน์ มั่นคง',             '083-300-3333', 'wirat@mail.com',   'เจ้าของ',  '2020-09-15', None),
            (11, 'บริษัท คอนเฟอเรนซ์ โปร จำกัด',  '02-666-1111',  'conf@mail.com',    'ผู้เช่า',  '2021-11-01', 'ห้องประชุมใหญ่'),
            (12, 'ฝ่ายบริหาร อาคาร C',            '02-777-1111',  'adminc@mail.com',  'เจ้าของ',  '2020-01-01', None),
        ]
        cursor.executemany("""INSERT INTO owners 
            (room_id, name, phone, email, owner_type, move_in_date, note)
            VALUES (?,?,?,?,?,?,?)""", owners)
    conn.commit()
    conn.close()
    print("Owners table ready!")
