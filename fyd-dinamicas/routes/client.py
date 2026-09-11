from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from database import get_db_connection
from parser.ticket_parser import TicketParser

client_bp = Blueprint('client', __name__)

def mask_phone(phone):
    """Enmascara el teléfono para proteger la privacidad del cliente."""
    clean_phone = ''.join(filter(str.isdigit, str(phone)))
    if len(clean_phone) >= 10:
        return f"{clean_phone[:4]}-XXX-{clean_phone[-4:]}"
    return "04XX-XXX-XXXX"

@client_bp.route('/')
def index():
    conn = get_db_connection()
    # Obtener dinámica activa
    dynamic = conn.execute("SELECT * FROM dynamycs WHERE status = 'ACTIVA' ORDER BY id DESC LIMIT 1").fetchone()

    total_tickets = 0
    draw_datetime = "2026-09-13T20:00"

    if dynamic:
        count_res = conn.execute("SELECT COUNT(*) FROM tickets WHERE dynamic_id = ?", (dynamic['id'],)).fetchone()
        total_tickets = count_res[0] if count_res else 0
        draw_datetime = dynamic['draw_datetime']

    conn.close()

    return render_template('client/index.html',
                           total_tickets=total_tickets,
                           draw_datetime=draw_datetime,
                           dynamic=dynamic)

@client_bp.route('/api/parse-ticket', methods=['POST'])
def parse_ticket():
    data = request.get_json()
    text = data.get('text', '')
    parsed = TicketParser.parse(text)
    return jsonify(parsed)

@client_bp.route('/register', methods=['POST'])
def register_ticket():
    conn = get_db_connection()
    dynamic = conn.execute("SELECT * FROM dynamycs WHERE status = 'ACTIVA' ORDER BY id DESC LIMIT 1").fetchone()

    if not dynamic:
        flash("No hay una dinámica activa en este momento.", "error")
        conn.close()
        return redirect(url_for('client.index'))

    name = request.form.get('name', '').strip()
    phone = request.form.get('phone', '').strip()
    raw_text = request.form.get('raw_text', '').strip()

    if not name or not phone or not raw_text:
        flash("Todos los campos son obligatorios.", "error")
        conn.close()
        return redirect(url_for('client.index'))

    # Procesar ticket
    parsed = TicketParser.parse(raw_text)

    if not parsed.get('serial'):
        flash("No se pudo extraer un SERIAL válido del texto pegado. Verifica el ticket.", "error")
        conn.close()
        return redirect(url_for('client.index'))

    serial = parsed['serial']

    # Verificar Duplicado por Serial
    existing = conn.execute("SELECT id FROM tickets WHERE extracted_serial = ?", (serial,)).fetchone()
    if existing:
        flash("Este serial ya fue registrado anteriormente.", "error")
        conn.close()
        return redirect(url_for('client.index'))

    # Generar correlativo de participación (#000001)
    last_ticket = conn.execute("SELECT id FROM tickets ORDER BY id DESC LIMIT 1").fetchone()
    next_id = (last_ticket['id'] + 1) if last_ticket else 1
    participation_num = f"#{next_id:06d}"

    # Guardar en base de datos como PENDIENTE
    conn.execute('''
        INSERT INTO tickets (dynamic_id, client_name, client_phone, raw_text, extracted_agency, extracted_serial, extracted_amount, participation_number, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'PENDIENTE')
    ''', (dynamic['id'], name, phone, raw_text, parsed['agency'], serial, parsed['amount'], participation_num))

    conn.commit()
    conn.close()

    return render_template('client/confirm.html',
                           participation_number=participation_num,
                           name=name,
                           serial=serial,
                           amount=parsed['amount'],
                           agency=parsed['agency'])

@client_bp.route('/api/public-stats')
def public_stats():
    conn = get_db_connection()
    dynamic = conn.execute("SELECT * FROM dynamycs WHERE status = 'ACTIVA' ORDER BY id DESC LIMIT 1").fetchone()

    if not dynamic:
        conn.close()
        return jsonify({'total': 0, 'draw_datetime': ''})

    total = conn.execute("SELECT COUNT(*) FROM tickets WHERE dynamic_id = ?", (dynamic['id'],)).fetchone()[0]
    conn.close()

    return jsonify({
        'total': total,
        'draw_datetime': dynamic['draw_datetime']
    })