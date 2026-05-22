from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from database import get_db, init_db, add_owners_table
import os

app = Flask(__name__)
app.secret_key = 'smart_building_secret_2024'

# ========== INIT ==========
@app.before_request
def setup():
    pass

# ========== DASHBOARD ==========
@app.route('/')
def index():
    db = get_db()
    stats = {
        'total_equipment': db.execute("SELECT COUNT(*) FROM equipment").fetchone()[0],
        'broken': db.execute("SELECT COUNT(*) FROM equipment WHERE status != 'ปกติ'").fetchone()[0],
        'pending': db.execute("SELECT COUNT(*) FROM maintenance_logs WHERE status = 'รอดำเนินการ'").fetchone()[0],
        'in_progress': db.execute("SELECT COUNT(*) FROM maintenance_logs WHERE status = 'กำลังดำเนินการ'").fetchone()[0],
        'total_cost': db.execute("SELECT SUM(cost) FROM maintenance_logs WHERE status = 'เสร็จสิ้น'").fetchone()[0] or 0,
        'total_buildings': db.execute("SELECT COUNT(*) FROM buildings").fetchone()[0],
    }
    recent_logs = db.execute("""
        SELECT ml.*, e.name as equipment_name, r.room_number, b.name as building_name, t.name as tech_name
        FROM maintenance_logs ml
        JOIN equipment e ON ml.equipment_id = e.id
        JOIN rooms r ON e.room_id = r.id
        JOIN buildings b ON r.building_id = b.id
        LEFT JOIN technicians t ON ml.technician_id = t.id
        ORDER BY ml.report_date DESC LIMIT 5
    """).fetchall()
    db.close()
    return render_template('index.html', stats=stats, recent_logs=recent_logs)

# ========== EQUIPMENT ==========
@app.route('/equipment')
def equipment_list():
    db = get_db()
    equipment = db.execute("""
        SELECT e.*, r.room_number, r.floor, b.name as building_name
        FROM equipment e
        JOIN rooms r ON e.room_id = r.id
        JOIN buildings b ON r.building_id = b.id
        ORDER BY e.id ASC
    """).fetchall()
    db.close()
    return render_template('equipment.html', equipment=equipment)

@app.route('/equipment/add', methods=['GET', 'POST'])
def equipment_add():
    db = get_db()
    if request.method == 'POST':
        db.execute("""
            INSERT INTO equipment (room_id, name, equipment_type, brand, model, serial_number, install_date, warranty_expire, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form['room_id'], request.form['name'], request.form['equipment_type'],
            request.form['brand'], request.form['model'], request.form['serial_number'],
            request.form['install_date'], request.form['warranty_expire'], request.form['status']
        ))
        db.commit()
        flash('เพิ่มอุปกรณ์สำเร็จ', 'success')
        db.close()
        return redirect(url_for('equipment_list'))
    rooms = db.execute("""
        SELECT r.id, r.room_number, b.name as building_name 
        FROM rooms r JOIN buildings b ON r.building_id = b.id
    """).fetchall()
    db.close()
    return render_template('equipment_form.html', rooms=rooms, equipment=None)

@app.route('/equipment/edit/<int:id>', methods=['GET', 'POST'])
def equipment_edit(id):
    db = get_db()
    if request.method == 'POST':
        db.execute("""
            UPDATE equipment SET room_id=?, name=?, equipment_type=?, brand=?, model=?,
            serial_number=?, install_date=?, warranty_expire=?, status=? WHERE id=?
        """, (
            request.form['room_id'], request.form['name'], request.form['equipment_type'],
            request.form['brand'], request.form['model'], request.form['serial_number'],
            request.form['install_date'], request.form['warranty_expire'], request.form['status'], id
        ))
        db.commit()
        flash('แก้ไขอุปกรณ์สำเร็จ', 'success')
        db.close()
        return redirect(url_for('equipment_list'))
    equipment = db.execute("SELECT * FROM equipment WHERE id=?", (id,)).fetchone()
    rooms = db.execute("""
        SELECT r.id, r.room_number, b.name as building_name 
        FROM rooms r JOIN buildings b ON r.building_id = b.id
    """).fetchall()
    db.close()
    return render_template('equipment_form.html', rooms=rooms, equipment=equipment)

@app.route('/equipment/delete/<int:id>', methods=['POST'])
def equipment_delete(id):
    db = get_db()
    db.execute("DELETE FROM equipment WHERE id=?", (id,))
    db.commit()
    db.close()
    flash('ลบอุปกรณ์สำเร็จ', 'warning')
    return redirect(url_for('equipment_list'))

# ========== MAINTENANCE LOGS ==========
@app.route('/maintenance')
def maintenance_list():
    db = get_db()
    logs = db.execute("""
        SELECT ml.*, e.name as equipment_name, r.room_number, b.name as building_name, t.name as tech_name
        FROM maintenance_logs ml
        JOIN equipment e ON ml.equipment_id = e.id
        JOIN rooms r ON e.room_id = r.id
        JOIN buildings b ON r.building_id = b.id
        LEFT JOIN technicians t ON ml.technician_id = t.id
        ORDER BY ml.report_date DESC
    """).fetchall()
    db.close()
    return render_template('maintenance.html', logs=logs)

@app.route('/maintenance/add', methods=['GET', 'POST'])
def maintenance_add():
    db = get_db()
    if request.method == 'POST':
        db.execute("""
            INSERT INTO maintenance_logs 
            (equipment_id, technician_id, report_date, issue_description, action_taken, cost, status, priority, completed_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            request.form['equipment_id'], request.form['technician_id'] or None,
            request.form['report_date'], request.form['issue_description'],
            request.form['action_taken'], request.form['cost'] or 0,
            request.form['status'], request.form['priority'],
            request.form['completed_date'] or None
        ))
        db.commit()
        flash('เพิ่มบันทึกซ่อมบำรุงสำเร็จ', 'success')
        db.close()
        return redirect(url_for('maintenance_list'))
    equipment = db.execute("""
        SELECT e.id, e.name, r.room_number, b.name as building_name
        FROM equipment e JOIN rooms r ON e.room_id = r.id JOIN buildings b ON r.building_id = b.id
    """).fetchall()
    technicians = db.execute("SELECT * FROM technicians").fetchall()
    db.close()
    return render_template('maintenance_form.html', equipment=equipment, technicians=technicians, log=None)

@app.route('/maintenance/edit/<int:id>', methods=['GET', 'POST'])
def maintenance_edit(id):
    db = get_db()
    if request.method == 'POST':
        db.execute("""
            UPDATE maintenance_logs SET equipment_id=?, technician_id=?, report_date=?,
            issue_description=?, action_taken=?, cost=?, status=?, priority=?, completed_date=?
            WHERE id=?
        """, (
            request.form['equipment_id'], request.form['technician_id'] or None,
            request.form['report_date'], request.form['issue_description'],
            request.form['action_taken'], request.form['cost'] or 0,
            request.form['status'], request.form['priority'],
            request.form['completed_date'] or None, id
        ))
        db.commit()
        flash('แก้ไขบันทึกสำเร็จ', 'success')
        db.close()
        return redirect(url_for('maintenance_list'))
    log = db.execute("SELECT * FROM maintenance_logs WHERE id=?", (id,)).fetchone()
    equipment = db.execute("""
        SELECT e.id, e.name, r.room_number, b.name as building_name
        FROM equipment e JOIN rooms r ON e.room_id = r.id JOIN buildings b ON r.building_id = b.id
    """).fetchall()
    technicians = db.execute("SELECT * FROM technicians").fetchall()
    db.close()
    return render_template('maintenance_form.html', equipment=equipment, technicians=technicians, log=log)

@app.route('/maintenance/delete/<int:id>', methods=['POST'])
def maintenance_delete(id):
    db = get_db()
    db.execute("DELETE FROM maintenance_logs WHERE id=?", (id,))
    db.commit()
    db.close()
    flash('ลบบันทึกสำเร็จ', 'warning')
    return redirect(url_for('maintenance_list'))

# ========== BUILDINGS & ROOMS ==========
@app.route('/buildings')
def buildings_list():
    db = get_db()
    buildings = db.execute("""
        SELECT b.*, COUNT(r.id) as room_count
        FROM buildings b LEFT JOIN rooms r ON b.id = r.building_id
        GROUP BY b.id
    """).fetchall()
    # ดึงห้องพร้อมเจ้าของแต่ละอาคาร
    rooms_with_owners = db.execute("""
        SELECT r.*, b.id as bid,
               o.name as owner_name, o.phone as owner_phone, o.owner_type
        FROM rooms r
        JOIN buildings b ON r.building_id = b.id
        LEFT JOIN owners o ON o.room_id = r.id
        ORDER BY r.building_id, r.floor, r.room_number
    """).fetchall()
    db.close()
    return render_template('buildings.html', buildings=buildings, rooms_with_owners=rooms_with_owners)

@app.route('/owners/add', methods=['GET','POST'])
def owner_add():
    db = get_db()
    if request.method == 'POST':
        db.execute("""INSERT INTO owners (room_id, name, phone, email, owner_type, move_in_date, note)
            VALUES (?,?,?,?,?,?,?)""",
            (request.form['room_id'], request.form['name'], request.form['phone'],
             request.form['email'], request.form['owner_type'],
             request.form['move_in_date'] or None, request.form['note']))
        db.commit()
        flash('เพิ่มเจ้าของ/ผู้เช่าสำเร็จ', 'success')
        db.close()
        return redirect(url_for('buildings_list'))
    rooms = db.execute("""SELECT r.id, r.room_number, b.name as building_name
        FROM rooms r JOIN buildings b ON r.building_id = b.id""").fetchall()
    db.close()
    return render_template('owner_form.html', rooms=rooms, owner=None)

@app.route('/owners/edit/<int:id>', methods=['GET','POST'])
def owner_edit(id):
    db = get_db()
    if request.method == 'POST':
        db.execute("""UPDATE owners SET room_id=?, name=?, phone=?, email=?,
            owner_type=?, move_in_date=?, note=? WHERE id=?""",
            (request.form['room_id'], request.form['name'], request.form['phone'],
             request.form['email'], request.form['owner_type'],
             request.form['move_in_date'] or None, request.form['note'], id))
        db.commit()
        flash('แก้ไขสำเร็จ', 'success')
        db.close()
        return redirect(url_for('buildings_list'))
    owner = db.execute("SELECT * FROM owners WHERE id=?", (id,)).fetchone()
    rooms = db.execute("""SELECT r.id, r.room_number, b.name as building_name
        FROM rooms r JOIN buildings b ON r.building_id = b.id""").fetchall()
    db.close()
    return render_template('owner_form.html', rooms=rooms, owner=owner)

@app.route('/owners/delete/<int:id>', methods=['POST'])
def owner_delete(id):
    db = get_db()
    db.execute("DELETE FROM owners WHERE id=?", (id,))
    db.commit()
    db.close()
    flash('ลบสำเร็จ', 'warning')
    return redirect(url_for('buildings_list'))

# ========== REPORT ==========
@app.route('/report')
def report():
    db = get_db()
    cost_by_month = db.execute("""
        SELECT strftime('%Y-%m', report_date) as month, SUM(cost) as total
        FROM maintenance_logs WHERE status='เสร็จสิ้น'
        GROUP BY month ORDER BY month DESC LIMIT 6
    """).fetchall()
    status_summary = db.execute("""
        SELECT status, COUNT(*) as count FROM maintenance_logs GROUP BY status
    """).fetchall()
    top_equipment = db.execute("""
        SELECT e.name, COUNT(ml.id) as repairs, SUM(ml.cost) as total_cost
        FROM maintenance_logs ml JOIN equipment e ON ml.equipment_id = e.id
        GROUP BY e.id ORDER BY repairs DESC LIMIT 5
    """).fetchall()
    db.close()
    return render_template('report.html', cost_by_month=cost_by_month,
                           status_summary=status_summary, top_equipment=top_equipment)

# ========== API (JSON) ==========
@app.route('/api/stats')
def api_stats():
    db = get_db()
    data = {
        'total_equipment': db.execute("SELECT COUNT(*) FROM equipment").fetchone()[0],
        'broken': db.execute("SELECT COUNT(*) FROM equipment WHERE status != 'ปกติ'").fetchone()[0],
        'pending': db.execute("SELECT COUNT(*) FROM maintenance_logs WHERE status='รอดำเนินการ'").fetchone()[0],
    }
    db.close()
    return jsonify(data)

if __name__ == "__main__":
    init_db()
    add_owners_table()
    app.run(debug=True, port=5000)
