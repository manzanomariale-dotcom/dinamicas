from datetime import datetime, timedelta
import re
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_socketio import SocketIO, emit

app = Flask(__name__)
app.secret_key = 'agencia_fyd_secret_key'

ADMIN_PASSWORD = '1234'

socketio = SocketIO(app, cors_allowed_origins='*')

DYNAMIC_CONFIG = {
    'title': 'Gran Dinámica Semanal',
    'min_amount': 200.0,
    'min_message': '¡Participan tickets de 200 Bs en adelante!',
    'target_draw_time': (datetime.now() + timedelta(days=2)).strftime(
        '%Y-%m-%dT20:00'
    ),
    'prize_1': '1er Lugar - Premio Mayor',
    'prize_2': '2do Lugar - Segundo Premio',
    'prize_3': '3er Lugar - Tercer Premio',
}

REGISTERED_TICKETS = [
    {
        'id': 1,
        'participation_number': '#000001',
        'client_name': 'Maria Perez',
        'client_phone': '04121234567',
        'extracted_serial': 'TQ987654',
        'extracted_amount': 600.0,
        'status': 'APROBADO',
        'raw_text': 'Ticket TQ987654 - Monto: 600 Bs.',
    },
]


def extract_ticket_data(text):
  amount = 0.0
  total_match = re.search(
      r'TOTAL\s*(?:TICKET)?\s*(?:\(BS\)|VES)?:?\s*([\d\.,]+)',
      text,
      re.IGNORECASE,
  )
  if total_match:
    raw_amount = total_match.group(1).replace('.', '').replace(',', '.')
    try:
      amount = float(raw_amount)
    except ValueError:
      amount = 0.0

  if amount == 0.0:
    lines = [
        l
        for l in text.split('\n')
        if 'PIN:' not in l and '/' not in l and 'Hora:' not in l
    ]
    cleaned_text = '\n'.join(lines)
    numbers = re.findall(r'(\d{1,3}(?:\.\d{3})*(?:,\d{2})?)', cleaned_text)
    for num in numbers:
      try:
        val = float(num.replace('.', '').replace(',', '.'))
        if val < 50000 and val > amount:
          amount = val
      except ValueError:
        continue

  serial = 'NO DETECTADO'
  sn_match = re.search(r'S/N:?\s*([A-Z0-9\-]+)', text, re.IGNORECASE)
  if sn_match:
    serial = sn_match.group(1)

  if serial == 'NO DETECTADO':
    hash_serial = re.search(r'Serial:\s*#?([A-Z0-9\-]+)#?', text, re.IGNORECASE)
    if hash_serial:
      serial = hash_serial.group(1)

  if serial == 'NO DETECTADO':
    link_serial = re.search(r'/v/([A-Z0-9\-]+)', text, re.IGNORECASE)
    if link_serial:
      serial = link_serial.group(1)

  if serial == 'NO DETECTADO':
    serial_match = re.search(
        r'SERIAL:?\s*[`"]*([A-Z0-9\-]+)[`"]*', text, re.IGNORECASE
    )
    if serial_match and serial_match.group(1).upper() != 'SERIAL':
      serial = serial_match.group(1)

  return serial, amount


@app.route('/')
def index():
  total_registered = len(REGISTERED_TICKETS)
  search_query = request.args.get('search_name', '').strip().lower()

  user_tickets = []
  if search_query:
    user_tickets = [
        t
        for t in REGISTERED_TICKETS
        if search_query in t['client_name'].lower()
    ]

  formatted_draw_time = DYNAMIC_CONFIG['target_draw_time'].replace('T', ' ')
  if len(formatted_draw_time) == 16:
    formatted_draw_time += ':00'

  return render_template(
      'index.html',
      total_registered=total_registered,
      target_draw_time=formatted_draw_time,
      user_tickets=user_tickets,
      search_query=search_query,
      config=DYNAMIC_CONFIG,
  )


@app.route('/upload-ticket', methods=['POST'])
def upload_ticket():
  client_name = request.form.get('client_name', '').strip()
  client_phone = request.form.get('client_phone', '').strip()
  raw_ticket = request.form.get('raw_ticket', '').strip()

  if not raw_ticket:
    flash('Debes pegar el texto del ticket.', 'error')
    return redirect(url_for('index'))

  serial, amount = extract_ticket_data(raw_ticket)

  if amount < DYNAMIC_CONFIG['min_amount']:
    flash(
        f"El monto mínimo para participar es de Bs."
        f" {DYNAMIC_CONFIG['min_amount']}. Tu ticket registra Bs. {amount}",
        'error',
    )
    return redirect(url_for('index'))

  new_id = len(REGISTERED_TICKETS) + 1
  new_number = f'#{new_id:06d}'

  ticket = {
      'id': new_id,
      'participation_number': new_number,
      'client_name': client_name,
      'client_phone': client_phone,
      'extracted_serial': serial,
      'extracted_amount': amount,
      'status': 'PENDIENTE',
      'raw_text': raw_ticket,
  }

  REGISTERED_TICKETS.append(ticket)

  flash(
      f'¡Ticket {new_number} registrado con éxito! Serial: {serial} - Bs.'
      f' {amount}',
      'success',
  )
  return redirect(url_for('index', search_name=client_name))


@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
  if request.method == 'POST':
    password_input = request.form.get('password', '')
    if password_input == ADMIN_PASSWORD:
      session['admin_logged'] = True
      flash('Sesión iniciada correctamente.', 'admin_success')
    else:
      flash('Contraseña incorrecta.', 'admin_error')
      return render_template('admin.html', logged_in=False)

  is_logged = session.get('admin_logged', False)
  if not is_logged:
    return render_template('admin.html', logged_in=False)

  approved_tickets = [
      t for t in REGISTERED_TICKETS if t['status'] == 'APROBADO'
  ]
  return render_template(
      'admin.html',
      logged_in=True,
      tickets=REGISTERED_TICKETS,
      approved_tickets=approved_tickets,
      config=DYNAMIC_CONFIG,
  )


@app.route('/admin/logout')
def admin_logout():
  session.pop('admin_logged', None)
  flash('Has cerrado sesión.', 'admin_success')
  return redirect(url_for('admin_panel'))


@app.route('/admin/update-config', methods=['POST'])
def update_config():
  if not session.get('admin_logged'):
    return redirect(url_for('admin_panel'))

  DYNAMIC_CONFIG['title'] = request.form.get(
      'title', DYNAMIC_CONFIG['title']
  ).strip()
  DYNAMIC_CONFIG['min_amount'] = float(
      request.form.get('min_amount', DYNAMIC_CONFIG['min_amount'])
  )
  DYNAMIC_CONFIG['target_draw_time'] = request.form.get(
      'target_draw_time', DYNAMIC_CONFIG['target_draw_time']
  )
  DYNAMIC_CONFIG['prize_1'] = request.form.get(
      'prize_1', DYNAMIC_CONFIG['prize_1']
  ).strip()
  DYNAMIC_CONFIG['prize_2'] = request.form.get(
      'prize_2', DYNAMIC_CONFIG['prize_2']
  ).strip()
  DYNAMIC_CONFIG['prize_3'] = request.form.get(
      'prize_3', DYNAMIC_CONFIG['prize_3']
  ).strip()

  flash('Configuración de la dinámica actualizada con éxito.', 'admin_success')
  return redirect(url_for('admin_panel'))


@app.route('/admin/update-status/<int:ticket_id>/<string:new_status>')
def update_status(ticket_id, new_status):
  if not session.get('admin_logged'):
    return redirect(url_for('admin_panel'))

  for ticket in REGISTERED_TICKETS:
    if ticket['id'] == ticket_id:
      ticket['status'] = new_status
      break
  return redirect(url_for('admin_panel'))


@app.route('/admin/delete/<int:ticket_id>')
def delete_ticket(ticket_id):
  if not session.get('admin_logged'):
    return redirect(url_for('admin_panel'))

  global REGISTERED_TICKETS
  REGISTERED_TICKETS = [t for t in REGISTERED_TICKETS if t['id'] != ticket_id]
  return redirect(url_for('admin_panel'))


# --- WEBSOCKETS ---


@socketio.on('spin_place')
def handle_spin(data):
  emit('start_spinning_place', data, broadcast=True)


@socketio.on('winner_place_selected')
def handle_winner_place(data):
  emit('show_place_winner', data, broadcast=True)


if __name__ == '__main__':
  socketio.run(app, debug=True, port=5000)
