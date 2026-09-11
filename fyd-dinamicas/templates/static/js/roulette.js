function spinWheel() {
    const btn = document.getElementById('spinBtn');
    btn.disabled = true;

    fetch('/admin/api/spin-wheel', { method: 'POST' })
        .then(res => res.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                btn.disabled = false;
                return;
            }

            const wheel = document.getElementById('wheel');
            // GIRO DE LA RULETA (ANIMACIÓN DE 5 SEGUNDOS)
            const randomDegrees = 360 * 5 + Math.floor(Math.random() * 360);
            wheel.style.transform = `rotate(${randomDegrees}deg)`;

            setTimeout(() => {
                // MOSTRAR GANADOR SELECCIONADO POR EL BACKEND
                document.getElementById('wName').innerText = data.client_name;
                document.getElementById('wNum').innerText = data.participation_number;
                document.getElementById('wPhone').innerText = data.masked_phone;
                document.getElementById('wSerial').innerText = data.serial;

                document.getElementById('winnerModal').style.display = 'flex';
            }, 5000);
        })
        .catch(err => {
            alert("Ocurrió un error en el servidor.");
            btn.disabled = false;
        });
}