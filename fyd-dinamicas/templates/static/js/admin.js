function viewText(text) {
    alert("TEXTO COMPLETO PEGADO POR EL CLIENTE:\n\n" + text);
}

function validateTicket(ticketId) {
    if (confirm("¿Confirmas la validación de este ticket? Entrará oficialmente a la ruleta.")) {
        fetch(`/admin/ticket/${ticketId}/validate`, { method: 'POST' })
            .then(res => res.json())
            .then(data => {
                if (data.success) location.reload();
            });
    }
}

function rejectTicket(ticketId) {
    const reason = prompt("Selecciona o escribe el motivo de rechazo:\n1. Serial ilegible\n2. Monto menor a Bs. 500\n3. No aparece Agencia FyD\n4. Ticket ganador\n5. Ticket repetido", "Monto menor a Bs. 500");
    if (reason) {
        fetch(`/admin/ticket/${ticketId}/reject`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reason: reason })
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) location.reload();
        });
    }
}