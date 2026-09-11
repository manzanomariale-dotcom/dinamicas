from flask import Blueprint, redirect, render_template, url_for

# Configuración del Blueprint para el módulo de administración
admin_bp = Blueprint('admin', __name__)


# Ruta principal del panel de administración (/admin)
@admin_bp.route('/admin')
def index():
  from app import REGISTERED_TICKETS

  return render_template('admin.html', tickets=REGISTERED_TICKETS)


# Cambiar estado de un ticket (Aprobar / Rechazar)
@admin_bp.route('/admin/update-status/<int:ticket_id>/<string:new_status>')
def update_status(ticket_id, new_status):
  from app import REGISTERED_TICKETS

  for ticket in REGISTERED_TICKETS:
    if ticket['id'] == ticket_id:
      ticket['status'] = new_status
      break
  return redirect(url_for('admin.index'))


# Eliminar ticket de la lista
@admin_bp.route('/admin/delete/<int:ticket_id>')
def delete_ticket(ticket_id):
  from app import REGISTERED_TICKETS

  REGISTERED_TICKETS[:] = [
      t for t in REGISTERED_TICKETS if t['id'] != ticket_id
  ]
  return redirect(url_for('admin.index'))