document.addEventListener('DOMContentLoaded', function() {
    // 1. CUENTA REGRESIVA
    const countdownEl = document.getElementById('countdown');
    if (countdownEl) {
        const targetStr = countdownEl.getAttribute('data-target');
        const targetDate = new Date(targetStr).getTime();

        function updateTimer() {
            const now = new Date().getTime();
            const diff = targetDate - now;

            if (diff <= 0) {
                document.getElementById('days').innerText = '00';
                document.getElementById('hours').innerText = '00';
                document.getElementById('mins').innerText = '00';
                document.getElementById('secs').innerText = '00';
                return;
            }

            const days = Math.floor(diff / (1000 * 60 * 60 * 24));
            const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const mins = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const secs = Math.floor((diff % (1000 * 60)) / 1000);

            document.getElementById('days').innerText = String(days).padStart(2, '0');
            document.getElementById('hours').innerText = String(hours).padStart(2, '0');
            document.getElementById('mins').innerText = String(mins).padStart(2, '0');
            document.getElementById('secs').innerText = String(secs).padStart(2, '0');
        }

        setInterval(updateTimer, 1000);
        updateTimer();
    }

    // 2. PARSER Y EXTRACTION EN VIVO AL PEGAR TICKET
    const rawText = document.getElementById('raw_text');
    const detectionBox = document.getElementById('detectionBox');

    if (rawText) {
        rawText.addEventListener('input', function() {
            const text = this.value;
            if (text.trim().length < 10) {
                detectionBox.style.display = 'none';
                return;
            }

            fetch('/api/parse-ticket', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text: text })
            })
            .then(res => res.json())
            .then(data => {
                detectionBox.style.display = 'block';
                document.getElementById('detAgency').innerText = data.agency;
                document.getElementById('detSerial').innerText = data.serial || 'No detectado';
                document.getElementById('detAmount').innerText = 'Bs. ' + data.amount;

                const msgEl = document.getElementById('detMessage');
                if (data.is_amount_valid && data.has_agency && data.serial) {
                    msgEl.innerHTML = '<span class="badge-valid">Tu ticket cumple con los requisitos y será enviado a revisión.</span>';
                } else if (!data.is_amount_valid) {
                    msgEl.innerHTML = '<span class="badge-invalid">El monto detectado debe ser mayor o igual a Bs. 500.</span>';
                } else {
                    msgEl.innerHTML = '<span class="badge-invalid">Revisa el texto pegado, faltan datos clave.</span>';
                }
            });
        });
    }
});