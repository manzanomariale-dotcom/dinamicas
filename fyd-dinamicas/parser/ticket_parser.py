import re

class TicketParser:
    @staticmethod
    def parse(text):
        """
        Analiza el texto completo pegado por el cliente para extraer:
        - Agencia FyD (Presencia)
        - Serial
        - Monto
        """
        if not text or not isinstance(text, str):
            return {
                'valid': False,
                'error': 'El texto del ticket está vacío.'
            }

        # 1. Verificar presencia de Agencia FyD
        agency_pattern = r'(?i)agencia\s*f\s*y\s*d|agencia\s*fyd'
        has_agency = bool(re.search(agency_pattern, text))
        extracted_agency = "Agencia FyD" if has_agency else None

        # 2. Extraer Serial
        # Busca líneas como "Serial: 839472123456", "SERIAL # 839472123456", etc.
        serial_pattern = r'(?i)serial\s*[:#\-]?\s*([A-Za-z0-9]+)'
        serial_match = re.search(serial_pattern, text)
        extracted_serial = serial_match.group(1).strip() if serial_match else None

        # Si no se encuentra con la palabra Serial, buscar secuencias numéricas largas (10-16 dígitos)
        if not extracted_serial:
            fallback_serial = re.search(r'\b\d{10,16}\b', text)
            if fallback_serial:
                extracted_serial = fallback_serial.group(0).strip()

        # 3. Extraer Monto
        # Busca patrones tipo: Bs. 750, Bs. 1.000, 750 Bs, Monto: 500, etc.
        amount_pattern = r'(?i)(?:bs\.?|monto[:\s]*)?\s*([\d\.,]+)\s*(?:bs\.?)?'
        # Mejor búsqueda enfocada en montos explícitos
        amount_matches = re.findall(r'(?i)(?:bs\.?\s*([\d\.,]+)|monto[:\s]*([\d\.,]+))', text)

        extracted_amount = None
        for match in amount_matches:
            val_str = match[0] or match[1]
            if val_str:
                # Normalizar formato de moneda (ej: 1.000,00 o 1,000.00 o 750)
                clean_val = val_str.replace('.', '').replace(',', '.') if ',' in val_str and val_str.rfind('.') < val_str.rfind(',') else val_str.replace(',', '')
                try:
                    val = float(clean_val)
                    if val > 0:
                        extracted_amount = val
                        break
                except ValueError:
                    continue

        if not extracted_amount:
            # Fallback simple
            raw_amounts = re.findall(r'\b\d+(?:[\.,]\d{1,2})?\b', text)
            for ra in raw_amounts:
                try:
                    val = float(ra.replace(',', '.'))
                    if val >= 50: # Evitar falsos positivos pequeños
                        extracted_amount = val
                        break
                except ValueError:
                    continue

        return {
            'has_agency': has_agency,
            'agency': extracted_agency or "No detectado",
            'serial': extracted_serial,
            'amount': extracted_amount or 0.0,
            'is_amount_valid': (extracted_amount or 0.0) >= 500.0
        }