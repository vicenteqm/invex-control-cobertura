"""
Motor de análisis de Control de Cobertura — puerto Python del motor JS ya validado.
Lee los mismos dos archivos (asistencia + base de tiendas) y produce exactamente
la misma estructura de datos que consume el dashboard (dict "RESULT").
"""
import re
import math
from datetime import datetime, date

DIAS_ES = ['LUNES', 'MARTES', 'MIERCOLES', 'JUEVES', 'VIERNES', 'SABADO', 'DOMINGO']


def to_min(hhmm):
    if not hhmm:
        return None
    m = re.match(r'^(\d{1,2}):(\d{2})', str(hhmm))
    if not m:
        return None
    return int(m.group(1)) * 60 + int(m.group(2))


def fmt_min(m):
    h, mm = divmod(int(m), 60)
    return f"{h:02d}:{mm:02d}"


def clean_time_cell(v):
    if v is None:
        return None
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        if v == 0:
            return None
        total_min = round(v * 24 * 60)
        if total_min <= 0:
            return None
        return fmt_min(total_min % 1440)
    if hasattr(v, 'hour'):  # datetime.time
        if v.hour == 0 and v.minute == 0 and v.second == 0:
            return None
        return f"{v.hour:02d}:{v.minute:02d}"
    s = str(v).strip()
    if s in ('', '00:00:00', '0'):
        return None
    m = re.match(r'^(\d{1,2}):(\d{2})', s)
    if not m:
        return None
    return f"{int(m.group(1)):02d}:{m.group(2)}"


def day_cols(day):
    base = 22 + (day - 1) * 3
    return base, base + 1, base + 2


def norm(s):
    return '' if s is None else str(s).strip().upper()


def parse_store_hours(h):
    if not h:
        return 600, 1200
    s = str(h).lower().replace('hrs', '').replace('hr', '').strip()
    parts = s.split('a')
    if len(parts) < 2:
        return 600, 1200
    try:
        o = int(parts[0].strip())
        c = int(parts[1].strip())
        return o * 60, c * 60
    except ValueError:
        return 600, 1200


def has_usuario(usuario):
    if not usuario:
        return False
    u = norm(usuario)
    return u not in ('', 'PENDIENTE', 'N/A')


def has_pandape(pin):
    if pin is None:
        return False
    s = str(pin).strip().upper()
    return s not in ('', '0', '0.0', 'NONE', 'PENDIENTE', 'N/A')


def load_maat_usuarios(rows, anio_esperado=None, mes_esperado=None):
    """Lee el concentrado de MAAT (header en la primera fila) y regresa
    (usuarios_por_dia, ubicacion_por_usuario_dia, dia_min, dia_max):
      - usuarios_por_dia: dict {día_del_mes: set(usuarios que registraron ESE día)}.
      - ubicacion_por_usuario_dia: dict {(usuario, día): 'nombre del punto de venta'}.
        MAAT registra dónde REALMENTE estuvo cada quien — usamos esto para avisar si
        un promotor apareció trabajando en una tienda distinta a la que tiene asignada
        en la asistencia, en vez de simplemente ignorarlo.
      - dia_min/dia_max: rango de días que cubre el archivo completo (solo informativo).

    Si se dan anio_esperado/mes_esperado, se IGNORAN todas las filas que no sean de
    ese año y mes exactos — esto es clave porque el export real de MAAT suele traer
    varios meses mezclados en el mismo archivo (p.ej. un archivo "de septiembre"
    puede traer también registros de agosto). Sin este filtro, el día 1 de agosto y
    el día 1 de septiembre se mezclarían solo por compartir el mismo número de día.

    Busca la columna 'EJECUTIVO' primero (así se llama en el export real de MAAT, con
    logins tipo 'nombre.apellido' que cruzan contra el campo USUARIO de la asistencia),
    y como respaldo también acepta 'USUARIO', 'USER' o 'LOGIN'."""
    if not rows:
        return {}, {}, None, None
    header = rows[0]
    col_idx = None
    for wanted in ('EJECUTIVO', 'USUARIO', 'USER', 'LOGIN'):
        for i, h in enumerate(header):
            if h and wanted in norm(h):
                col_idx = i
                break
        if col_idx is not None:
            break
    if col_idx is None:
        raise ValueError("No encontré ninguna columna 'EJECUTIVO' (ni 'USUARIO'/'USER'/'LOGIN') "
                          "en el encabezado del archivo de MAAT. Encabezados encontrados: "
                          + ', '.join(str(h) for h in header if h))
    fecha_idx = None
    for i, h in enumerate(header):
        if h and 'FECHA' in norm(h):
            fecha_idx = i
            break
    if fecha_idx is None:
        raise ValueError("No encontré ninguna columna 'Fecha' en el archivo de MAAT — se necesita "
                          "para saber en qué día registró cada quien y comparar contra el día de hoy.")
    punto_idx = None
    for i, h in enumerate(header):
        if h and 'SEGUNDO PUNTO DE VENTA' in norm(h):
            punto_idx = i
            break
    if punto_idx is None:
        for i, h in enumerate(header):
            if h and 'PUNTO DE VENTA' in norm(h):
                punto_idx = i
                break
    entrada_idx = None
    for i, h in enumerate(header):
        if h and 'HORARIO DE ENTRADA' in norm(h):
            entrada_idx = i
            break
    salida_idx = None
    for i, h in enumerate(header):
        if h and 'HORARIO DE SALIDA' in norm(h):
            salida_idx = i
            break
    cierre_manual_idx = None
    for i, h in enumerate(header):
        if h and 'CERR' in norm(h) and 'JORNADA' in norm(h):
            cierre_manual_idx = i
            break

    usuarios_por_dia = {}
    ubicacion_por_usuario_dia = {}
    entrada_por_usuario_dia = {}
    salida_por_usuario_dia = {}
    cierre_manual_por_usuario_dia = {}
    filas_de_otro_mes = 0
    for row in rows[1:]:
        if col_idx >= len(row) or not row[col_idx]:
            continue
        if fecha_idx >= len(row) or not row[fecha_idx]:
            continue
        fecha = _parse_fecha_completa(row[fecha_idx])
        if not fecha:
            continue
        anio, mes, d = fecha
        if anio_esperado and mes_esperado and (anio, mes) != (anio_esperado, mes_esperado):
            filas_de_otro_mes += 1
            continue
        u = norm(row[col_idx])
        if not u:
            continue
        usuarios_por_dia.setdefault(d, set()).add(u)
        if punto_idx is not None and punto_idx < len(row) and row[punto_idx]:
            ubicacion_por_usuario_dia[(u, d)] = str(row[punto_idx]).strip()
        if entrada_idx is not None and entrada_idx < len(row) and row[entrada_idx]:
            hora = _parse_hora_hhmm(row[entrada_idx])
            if hora:
                # si hay varios registros el mismo día, nos quedamos con la hora más temprana
                clave = (u, d)
                if clave not in entrada_por_usuario_dia or hora < entrada_por_usuario_dia[clave]:
                    entrada_por_usuario_dia[clave] = hora
        if salida_idx is not None and salida_idx < len(row) and row[salida_idx]:
            hora_s = _parse_hora_hhmm(row[salida_idx])
            if hora_s:
                # nos quedamos con la hora de salida MÁS TARDÍA del día (la última vez que se le vio)
                clave = (u, d)
                if clave not in salida_por_usuario_dia or hora_s > salida_por_usuario_dia[clave]:
                    salida_por_usuario_dia[clave] = hora_s
        if cierre_manual_idx is not None and cierre_manual_idx < len(row) and row[cierre_manual_idx]:
            # si CUALQUIER registro del día dice que cerró jornada manualmente, lo marcamos así
            if str(row[cierre_manual_idx]).strip().upper() == 'SI':
                cierre_manual_por_usuario_dia[(u, d)] = True

    dias = list(usuarios_por_dia.keys())
    dia_min = min(dias) if dias else None
    dia_max = max(dias) if dias else None
    return (usuarios_por_dia, ubicacion_por_usuario_dia, entrada_por_usuario_dia, salida_por_usuario_dia,
            cierre_manual_por_usuario_dia, dia_min, dia_max)


def _parse_hora_hhmm(valor):
    """Extrae 'HH:MM' de una celda de hora de MAAT (viene como texto plano tipo '11:57')."""
    if hasattr(valor, 'hour'):
        return f"{valor.hour:02d}:{valor.minute:02d}"
    s = str(valor).strip()
    m = re.match(r'^(\d{1,2}):(\d{2})', s)
    if m:
        return f"{int(m.group(1)):02d}:{m.group(2)}"
    return None


def _parse_fecha_completa(valor):
    """Regresa (año, mes, día) de una celda de fecha, sin importar si viene como texto
    'YYYY-MM-DD', 'DD/MM/YYYY' (formato usado en México — puede venir MEZCLADO con el
    anterior en el mismo archivo, e incluso con MESES distintos en el mismo archivo),
    objeto date/datetime, u otro formato común. Regresar año+mes (no solo el día) es lo
    que evita que, por ejemplo, el 1 de agosto y el 1 de septiembre se confundan solo
    por compartir el mismo número de día."""
    if hasattr(valor, 'year'):
        return valor.year, valor.month, valor.day
    s = str(valor).strip()
    m = re.match(r'^(\d{4})-(\d{1,2})-(\d{1,2})', s)   # YYYY-MM-DD
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    m = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})', s)   # DD/MM/YYYY
    if m:
        return int(m.group(3)), int(m.group(2)), int(m.group(1))
    return None


def registro_categoria(registra_pandape, registra_maat):
    if registra_pandape and registra_maat:
        return 'COMPLETO'
    if registra_pandape and not registra_maat:
        return 'SEGUIMIENTO_MAAT'      # tiene Pandape, falta registrarse en MAAT
    if registra_maat and not registra_pandape:
        return 'ALERTA_PANDAPE'        # tiene MAAT, falta registrarse en Pandape
    return 'ALARMANTE'                 # no está registrado en ninguno


def parse_shift_start(horario_personal, fallback_min=None):
    """Extrae la hora de inicio de turno de un texto libre como 'L-D 10:00 - 20:00'.
    Si no puede parsear, regresa fallback_min (p.ej. la apertura de la tienda)."""
    if horario_personal:
        m = re.search(r'(\d{1,2}):(\d{2})', str(horario_personal))
        if m:
            return int(m.group(1)) * 60 + int(m.group(2))
    return fallback_min


def parse_shift_end(horario_personal):
    """Extrae la hora de FIN de turno de un texto libre como 'L-D 10:00 - 20:00'
    (el segundo HH:MM que aparece). Regresa None si no se puede determinar."""
    if horario_personal:
        matches = re.findall(r'(\d{1,2}):(\d{2})', str(horario_personal))
        if len(matches) >= 2:
            h, m = matches[1]
            return int(h) * 60 + int(m)
    return None


def merge_intervals(intervals):
    if not intervals:
        return []
    s = sorted(intervals)
    merged = [list(s[0])]
    for a, b in s[1:]:
        if a <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], b)
        else:
            merged.append([a, b])
    return merged


def gaps_from(open_m, close_m, covered):
    gaps = []
    cur = open_m
    for a, b in covered:
        cs, ce = max(a, open_m), min(b, close_m)
        if cs > cur:
            gaps.append((cur, cs))
        cur = max(cur, ce)
    if cur < close_m:
        gaps.append((cur, close_m))
    return gaps


def detect_days_in_month(header_row):
    count = 0
    for d in range(1, 32):
        col = 22 + (d - 1) * 3
        v = header_row[col] if col < len(header_row) else None
        if v is not None and str(v).strip() != '':
            try:
                int(float(v))
                count = d
                continue
            except (ValueError, TypeError):
                break
        else:
            break
    return count or 31


def validate_headers(header_a, header_b):
    problems = []
    check_a = [(6, 'SOCIO'), (7, 'NOMBRE'), (9, 'NOMBRE'), (10, 'ESTATUS'), (11, 'USUARIO')]
    for idx, kw in check_a:
        v = norm(header_a[idx]) if idx < len(header_a) else ''
        if kw not in v:
            problems.append(f"Asistencia: se esperaba una columna con '{kw}' en la posición {idx+1}, se encontró '{header_a[idx] if idx < len(header_a) else '(vacío)'}'.")
    check_b = [(9, 'TIENDA'), (19, 'ESTATUS'), (20, 'HORARIO'), (25, 'PLANTILLA')]
    for idx, kw in check_b:
        v = norm(header_b[idx]) if idx < len(header_b) else ''
        if kw not in v:
            problems.append(f"Base de tiendas: se esperaba una columna con '{kw}' en la posición {idx+1}, se encontró '{header_b[idx] if idx < len(header_b) else '(vacío)'}'.")
    return problems


def build_employees(rows, days_in_month):
    employees = []
    for row in rows[1:]:
        if not row:
            continue
        tienda_key = str(row[6]).strip() if len(row) > 6 and row[6] else None
        if not tienda_key:
            # Respaldo por si "SOCIO Y NUMERO DE TIENDA" es una fórmula sin valor cacheado.
            socio = str(row[4]).strip() if len(row) > 4 and row[4] else ''
            det = str(row[5]).strip() if len(row) > 5 and row[5] else ''
            if socio and det:
                tienda_key = f"{socio} {det}"
        if not tienda_key:
            continue
        emp = {
            'region': row[1] if len(row) > 1 else None,
            'estado': row[2] if len(row) > 2 else None,
            'ciudad': row[3] if len(row) > 3 else None,
            'socio': row[4] if len(row) > 4 else None,
            'det': row[5] if len(row) > 5 else None,
            'tienda_key': tienda_key,
            'tienda_nombre': row[7] if len(row) > 7 else None,
            'puesto': row[8] if len(row) > 8 else None,
            'nombre': row[9] if len(row) > 9 else None,
            'estatus': str(row[10]).strip() if len(row) > 10 and row[10] else (row[10] if len(row) > 10 else None),
            'usuario': row[11] if len(row) > 11 else None,
            'pin_pandape': row[13] if len(row) > 13 else None,
            'jornada': row[14] if len(row) > 14 else None,
            'horario_personal': row[15] if len(row) > 15 else None,
            'fecha_alta': row[16] if len(row) > 16 else None,
            'fecha_ingreso': row[17] if len(row) > 17 else None,
            'fecha_baja': row[18] if len(row) > 18 else None,
            'descanso_oficial': row[20] if len(row) > 20 else None,
            'dias': {}
        }
        for d in range(1, days_in_month + 1):
            mc, ec, sc = day_cols(d)
            marker = row[mc] if mc < len(row) else None
            entr = clean_time_cell(row[ec]) if ec < len(row) else None
            sal = clean_time_cell(row[sc]) if sc < len(row) else None
            if (marker is None or marker == '') and entr is None and sal is None:
                continue
            emp['dias'][d] = {'code': marker, 'entrada': entr, 'salida': sal}
        employees.append(emp)
    return employees


def build_stores(rows):
    stores = {}
    duplicados = {}   # key -> cuántas veces apareció (para detectar filas que se pisan entre sí)
    filas_sin_key = 0
    for row in rows[1:]:
        if not row:
            continue
        key = str(row[9]).strip() if len(row) > 9 and row[9] else None
        if not key:
            # Respaldo: en algunos archivos "SOCIO + NUM DE TIENDA" es una fórmula y su
            # valor cacheado se puede perder al reabrir/guardar el archivo. Si pasa eso,
            # reconstruimos la clave a partir de SOCIO + NUMERO DE TIENDA (columnas fijas).
            socio = str(row[7]).strip() if len(row) > 7 and row[7] else ''
            num = str(row[8]).strip() if len(row) > 8 and row[8] else ''
            if socio and num:
                key = f"{socio} {num}"
        if not key:
            filas_sin_key += 1
            continue
        if key in stores:
            duplicados[key] = duplicados.get(key, 1) + 1
        ejecutiva = None
        for idx in (36, 30, 28, 32):
            if len(row) > idx and row[idx]:
                ejecutiva = row[idx]
                break
        sublider = None
        for idx in (32, 27):
            if len(row) > idx and row[idx] and not isinstance(row[idx], (int, float)):
                sublider = row[idx]
                break
        stores[key] = {
            'key': key,
            'proyecto': row[0] if len(row) > 0 else None,
            'zona': row[1] if len(row) > 1 else None,
            'region': row[3] if len(row) > 3 else None,
            'subregion': row[4] if len(row) > 4 else None,
            'estado': row[5] if len(row) > 5 else None,
            'ciudad': row[6] if len(row) > 6 else None,
            'socio': row[7] if len(row) > 7 else None,
            'num_tienda': row[8] if len(row) > 8 else None,
            'tienda_nombre': row[10] if len(row) > 10 else None,
            'estatus': row[19] if len(row) > 19 else None,
            'horario': row[20] if len(row) > 20 else None,
            'plantilla_autorizada': float(row[25]) if len(row) > 25 and row[25] else 0,
            'ejecutiva': ejecutiva or 'Sin asignar',
            'sublider': sublider,
        }
    diagnostico = {
        'total_filas': len([r for r in rows[1:] if r]),
        'filas_sin_key': filas_sin_key,
        'claves_unicas': len(stores),
        'claves_duplicadas': duplicados,  # key -> num de filas repetidas que se pisaron
    }
    return stores, diagnostico


def _es_del_mes(valor, anio, mes):
    """True si una celda de fecha (texto, date o datetime) cae dentro del año/mes dados."""
    if not valor or not anio or not mes:
        return False
    if hasattr(valor, 'year'):
        return valor.year == anio and valor.month == mes
    s = str(valor).strip()
    m = re.match(r'^(\d{4})-(\d{1,2})', s)          # YYYY-MM-DD
    if m:
        return int(m.group(1)) == anio and int(m.group(2)) == mes
    m = re.match(r'^(\d{1,2})/(\d{1,2})/(\d{4})', s)  # DD/MM/YYYY
    if m:
        return int(m.group(3)) == anio and int(m.group(2)) == mes
    return False


def _build_num_lookup(stores):
    """Índice {NUMERO_DE_TIENDA: key} — la columna 'Segundo punto de venta' de MAAT
    trae justo ese número al principio (ej. '6563 TUXTLA GUTIÉRREZ'), que es el mismo
    NUMERO DE TIENDA/DETERMINANTE de la base de tiendas y de la asistencia de Pandape."""
    lookup = {}
    for key, s in stores.items():
        num = s.get('num_tienda')
        if num is None:
            continue
        try:
            num_int = int(str(num).strip())
            lookup[num_int] = key
        except (ValueError, TypeError):
            pass
    return lookup


def _resolver_tienda_de_maat(punto_venta, num_lookup):
    """Identifica a qué tienda se refiere el 'Segundo punto de venta' de MAAT, que
    trae el número de tienda/determinante al inicio del texto (ej. '6563 TUXTLA
    GUTIÉRREZ' → 6563). Si no hay un número reconocible al inicio, o ese número no
    existe en la base de tiendas, no se puede resolver — se ignora en vez de
    arriesgar un falso positivo."""
    if not punto_venta:
        return None
    texto = str(punto_venta).strip()
    m = re.match(r'^0*(\d{1,6})\b', texto)
    if not m:
        return None
    return num_lookup.get(int(m.group(1)))


def _calcular_registro_dia(e, key, day, stores, maat_usuarios_por_dia, maat_ubicacion_por_usuario_dia,
                            maat_entrada_por_usuario_dia, maat_salida_por_usuario_dia,
                            maat_cierre_manual_por_usuario_dia, num_lookup):
    """Calcula el registro Pandape/MAAT de un empleado para UN día específico
    (no acumulado) — se reutiliza tanto para 'hoy' como para poder consultar
    cualquier otro día del mes desde el panel."""
    info_dia = e['dias'].get(day)
    registra_pandape = bool(info_dia and info_dia['code'] in ('A', 'R'))
    maat_usuarios_dia = maat_usuarios_por_dia.get(day, set())
    registra_maat = norm(e['usuario']) in maat_usuarios_dia

    tienda_maat = maat_ubicacion_por_usuario_dia.get((norm(e['usuario']), day))
    se_movio_de_tienda = False
    tienda_maat_resuelta = None
    tienda_maat_key = None
    if tienda_maat:
        key_resuelta = _resolver_tienda_de_maat(tienda_maat, num_lookup)
        if key_resuelta:
            nombre_resuelto = stores[key_resuelta]['tienda_nombre'] or key_resuelta
            if key_resuelta != key:
                se_movio_de_tienda = True
                tienda_maat_key = key_resuelta
                tienda_maat_resuelta = f"{nombre_resuelto} ({key_resuelta})"
            else:
                tienda_maat_resuelta = nombre_resuelto

    hora_entrada_pandape = info_dia['entrada'] if (info_dia and registra_pandape) else None
    hora_entrada_maat = maat_entrada_por_usuario_dia.get((norm(e['usuario']), day)) if registra_maat else None
    hora_salida_pandape = info_dia['salida'] if (info_dia and registra_pandape) else None
    hora_salida_maat = maat_salida_por_usuario_dia.get((norm(e['usuario']), day)) if registra_maat else None
    cerro_jornada_manual = bool(maat_cierre_manual_por_usuario_dia.get((norm(e['usuario']), day))) if registra_maat else False

    # Horario que debía cumplir ese día: primero intentamos su horario personal explícito
    # (columna HORARIO, texto tipo 'L - D 11:00 - 20:00'). Si esa columna no trae un rango
    # de horas válido (pasa seguido: a veces trae el día de descanso por error de captura),
    # usamos como respaldo el tipo de JORNADA (Tiempo completo / Medio tiempo) cruzado con
    # el horario de la tienda — a Tiempo completo se le espera el horario completo de la
    # tienda; a Medio tiempo no se le puede adivinar con certeza cuál mitad le toca, así
    # que en ese caso no se compara (para no arriesgar una alerta falsa).
    hora_inicio_prog_min = parse_shift_start(e.get('horario_personal'))
    hora_fin_prog_min = parse_shift_end(e.get('horario_personal'))
    fuente_horario = 'horario_personal' if (hora_inicio_prog_min is not None or hora_fin_prog_min is not None) else None
    if hora_fin_prog_min is None and hora_inicio_prog_min is None:
        jornada_tipo = norm(e.get('jornada'))
        if 'TIEMPO COMPLETO' in jornada_tipo:
            open_m, close_m = parse_store_hours(stores.get(key, {}).get('horario'))
            hora_inicio_prog_min, hora_fin_prog_min = open_m, close_m
            fuente_horario = 'jornada_tiempo_completo'

    llego_tarde = False
    salio_antes_de_horario = False
    hora_inicio_programada = fmt_min(hora_inicio_prog_min) if hora_inicio_prog_min is not None else None
    hora_fin_programada = fmt_min(hora_fin_prog_min) if hora_fin_prog_min is not None else None
    minutos_tarde = None
    minutos_antes = None

    if hora_inicio_prog_min is not None:
        # la entrada más TEMPRANA que tengamos entre los dos sistemas (quien llegó primero)
        entradas = [to_min(h) for h in (hora_entrada_pandape, hora_entrada_maat) if h]
        entrada_real_min = min(entradas) if entradas else None
        if entrada_real_min is not None and entrada_real_min > hora_inicio_prog_min + 30:
            llego_tarde = True
            minutos_tarde = entrada_real_min - hora_inicio_prog_min

    if hora_fin_prog_min is not None:
        # la salida más TARDÍA que tengamos entre los dos sistemas (la última vez que se le vio)
        salidas = [to_min(h) for h in (hora_salida_pandape, hora_salida_maat) if h]
        salida_real_min = max(salidas) if salidas else None
        if salida_real_min is not None and salida_real_min < hora_fin_prog_min - 30:
            salio_antes_de_horario = True
            minutos_antes = hora_fin_prog_min - salida_real_min

    return {
        'registra_pandape': registra_pandape,
        'registra_maat': registra_maat,
        'estatus_registro': registro_categoria(registra_pandape, registra_maat),
        'tienda_maat': tienda_maat_resuelta or tienda_maat,
        'tienda_maat_key': tienda_maat_key,
        'se_movio_de_tienda': se_movio_de_tienda,
        'hora_entrada_pandape': hora_entrada_pandape,
        'hora_entrada_maat': hora_entrada_maat,
        'hora_salida_pandape': hora_salida_pandape,
        'hora_salida_maat': hora_salida_maat,
        'cerro_jornada_manual': cerro_jornada_manual,
        'fuente_horario_programado': fuente_horario,
        'hora_inicio_programada': hora_inicio_programada,
        'hora_fin_programada': hora_fin_programada,
        'llego_tarde': llego_tarde,
        'minutos_tarde': minutos_tarde,
        'salio_antes_de_horario': salio_antes_de_horario,
        'minutos_antes_de_hora': minutos_antes,
    }


def semaforo(activos_n, cobertura_pct, faltantes_hoy, riesgo_usuario, pct_usuario):
    if activos_n == 0:
        return 'ALARMANTE'  # la tienda no tiene ni un solo promotor activo asignado
    if riesgo_usuario:
        return 'ALARMANTE'
    if activos_n == 1:
        return 'CRITICA'
    if cobertura_pct >= 85 and pct_usuario >= 100:
        return 'OPTIMA'
    return 'RIESGO'


def analyze(employee_rows, store_rows, days_in_month, reference_day_override=None, hora_corte_min=None,
            anio=None, mes=None, maat_usuarios_por_dia=None, maat_ubicacion_por_usuario_dia=None,
            maat_entrada_por_usuario_dia=None, maat_salida_por_usuario_dia=None,
            maat_cierre_manual_por_usuario_dia=None, maat_dia_min=None, maat_dia_max=None):
    maat_cargado = maat_usuarios_por_dia is not None
    maat_usuarios_por_dia = maat_usuarios_por_dia or {}
    maat_ubicacion_por_usuario_dia = maat_ubicacion_por_usuario_dia or {}
    maat_entrada_por_usuario_dia = maat_entrada_por_usuario_dia or {}
    maat_salida_por_usuario_dia = maat_salida_por_usuario_dia or {}
    maat_cierre_manual_por_usuario_dia = maat_cierre_manual_por_usuario_dia or {}
    employees = build_employees(employee_rows, days_in_month)
    stores, stores_diag = build_stores(store_rows)

    # Nombre del día de la semana para cada número de día del mes (para no marcar como
    # falta a alguien cuyo descanso oficial semanal cae justo ese día).
    weekday_by_day = {}
    if anio and mes:
        for d in range(1, days_in_month + 1):
            try:
                weekday_by_day[d] = DIAS_ES[date(anio, mes, d).weekday()]
            except ValueError:
                pass

    by_store = {}
    for e in employees:
        by_store.setdefault(e['tienda_key'], []).append(e)

    last_day_with_data = 0
    for e in employees:
        if e['estatus'] != 'ACTIVO':
            continue
        for dk in e['dias'].keys():
            if dk > last_day_with_data:
                last_day_with_data = dk
    reference_day = reference_day_override or (last_day_with_data or days_in_month)

    # Comparación Pandape vs MAAT: SOLO del día de corte actual (reference_day),
    # no acumulado del mes — así no se mezclan periodos distintos.
    maat_usuarios_hoy = maat_usuarios_por_dia.get(reference_day, set())
    maat_tiene_datos_hoy = reference_day in maat_usuarios_por_dia
    num_lookup = _build_num_lookup(stores) if maat_cargado else {}

    store_results = {}
    estatus_counts = {}
    for s in stores.values():
        k = norm(s['estatus']) or '(vacío)'
        estatus_counts[k] = estatus_counts.get(k, 0) + 1
    # Acumulado global día por día, para las gráficas de tendencia
    resumen_diario = {d: {'asistencias': 0, 'faltas': 0, 'descansos': 0, 'pendientes': 0,
                           'ALARMANTE': 0, 'CRITICA': 0, 'RIESGO': 0, 'OPTIMA': 0, 'SIN_DATOS': 0}
                       for d in range(1, days_in_month + 1)}

    for key, store in stores.items():
        if norm(store['estatus']) != 'OPERANDO':
            continue
        open_m, close_m = parse_store_hours(store['horario'])
        emp_list = by_store.get(key, [])
        activos = [e for e in emp_list if e['estatus'] == 'ACTIVO']
        N = store['plantilla_autorizada'] or 0

        # Solo bajas/altas registradas EN ESTE MES (no cualquier fecha histórica que
        # traiga la fila) — si no sabemos el año/mes exacto, no contamos ninguna en
        # vez de arriesgarnos a mezclar meses distintos.
        bajas_mes = sum(1 for e in emp_list if _es_del_mes(e['fecha_baja'], anio, mes))
        altas_mes = sum(1 for e in emp_list if _es_del_mes(e['fecha_ingreso'], anio, mes))
        rotacion_pct = (bajas_mes / N * 100) if N > 0 else 0

        day_metrics = {}
        for day in range(1, days_in_month + 1):
            events = []
            rest_people, absent_people, pending_people = [], [], []
            presentes_n, usuarios_activos_n = 0, 0
            for e in activos:
                info = e['dias'].get(day)
                if not info:
                    continue
                code = info['code']
                ent, sal = to_min(info['entrada']), to_min(info['salida'])
                if code == 'D' and ent is None and sal is None:
                    rest_people.append(e['nombre']); continue
                if code == 'F' and ent is None and sal is None:
                    # Si ese día de la semana es su descanso oficial, no es una falta real
                    # aunque el archivo lo haya marcado como F — es su día de descanso.
                    dow = weekday_by_day.get(day)
                    if dow and norm(e['descanso_oficial']) == dow:
                        rest_people.append(e['nombre']); continue
                    # Si es el día de hoy y aún no llega la hora de corte a la hora en que
                    # inicia su turno, no es una falta real: el sistema simplemente no ha
                    # llegado a la hora en que le toca checar.
                    if day == reference_day and hora_corte_min is not None:
                        turno_inicio = parse_shift_start(e['horario_personal'], open_m)
                        if hora_corte_min < turno_inicio:
                            pending_people.append(e['nombre'])
                            continue
                    absent_people.append(e['nombre']); continue
                if ent is not None and sal is not None and sal > ent:
                    events.append((ent, sal, e['nombre'], code))
                    presentes_n += 1
                    if has_usuario(e['usuario']):
                        usuarios_activos_n += 1
                elif ent is not None and sal is None and code != 'F':
                    events.append((ent, close_m, e['nombre'], (code or '') + '*'))
                    presentes_n += 1
                    if has_usuario(e['usuario']):
                        usuarios_activos_n += 1

            covered = merge_intervals([(max(s, open_m), min(e, close_m)) for s, e, _, _ in events if max(s, open_m) < min(e, close_m)])
            gaps = gaps_from(open_m, close_m, covered)
            cobertura_pct = min(100, (presentes_n / N * 100)) if N > 0 else (100 if presentes_n > 0 else 0)
            pct_usuario = (usuarios_activos_n / presentes_n * 100) if presentes_n > 0 else 100
            riesgo_usuario = len(activos) > 0 and usuarios_activos_n == 0
            sem = 'SIN_DATOS' if len(emp_list) == 0 else semaforo(
                len(activos), cobertura_pct, len(absent_people), riesgo_usuario, pct_usuario
            )
            day_metrics[day] = {
                'day': day, 'presentes': presentes_n, 'faltantes_hoy': len(absent_people),
                'descansos_hoy': len(rest_people), 'pendientes_hoy': len(pending_people),
                'usuarios_activos': usuarios_activos_n,
                'cobertura_pct': round(cobertura_pct, 1), 'pct_usuario': round(pct_usuario, 1),
                'riesgo_usuario': riesgo_usuario, 'semaforo': sem,
                'gaps': [{'inicio': fmt_min(a), 'fin': fmt_min(b)} for a, b in gaps],
                'covered': [{'inicio': fmt_min(max(a, open_m)), 'fin': fmt_min(min(b, close_m))} for a, b in covered],
                'turnos': [{'empleado': n, 'entrada': fmt_min(s), 'salida': fmt_min(e), 'codigo': c}
                           for s, e, n, c in sorted(events)],
                'descansaron': rest_people, 'faltaron': absent_people, 'pendientes': pending_people,
            }
            rd = resumen_diario[day]
            rd['asistencias'] += presentes_n
            rd['faltas'] += len(absent_people)
            rd['descansos'] += len(rest_people)
            rd['pendientes'] += len(pending_people)
            rd[sem] += 1

        hoy = day_metrics.get(reference_day)
        ayer = day_metrics.get(reference_day - 1)
        reincidencia = 'ESTABLE'
        if hoy and ayer:
            hoy_crit = hoy['semaforo'] in ('CRITICA', 'ALARMANTE')
            ayer_crit = ayer['semaforo'] in ('CRITICA', 'ALARMANTE')
            if hoy_crit and ayer_crit:
                reincidencia = 'REINCIDENTE'
            elif hoy_crit and not ayer_crit:
                reincidencia = 'NUEVO_DETERIORO'
            elif hoy['semaforo'] == 'OPTIMA' and ayer_crit:
                reincidencia = 'RECUPERADA'

        dias_rojo, suma_cobertura, dias_con_datos = 0, 0, 0
        for d in range(1, reference_day + 1):
            dm = day_metrics.get(d)
            if not dm:
                continue
            dias_con_datos += 1
            suma_cobertura += dm['cobertura_pct']
            if dm['semaforo'] in ('CRITICA', 'ALARMANTE'):
                dias_rojo += 1
        promedio_mensual = round(suma_cobertura / dias_con_datos, 1) if dias_con_datos else 0

        empleados_activos = []
        for e in activos:
            faltas = asistencias = retardos = 0
            for d in range(1, reference_day + 1):
                info = e['dias'].get(d)
                if not info:
                    continue
                if info['code'] == 'F':
                    faltas += 1
                elif info['code'] == 'A':
                    asistencias += 1
                elif info['code'] == 'R':
                    retardos += 1

            # Registro Pandape/MAAT: se calcula día por día (nunca acumulado), y se
            # guarda para TODOS los días del mes para poder consultar cualquier día
            # desde el panel, no solo el día de corte de hoy.
            registro_por_dia = {}
            if maat_cargado:
                for d in range(1, days_in_month + 1):
                    registro_por_dia[d] = _calcular_registro_dia(
                        e, key, d, stores, maat_usuarios_por_dia, maat_ubicacion_por_usuario_dia,
                        maat_entrada_por_usuario_dia, maat_salida_por_usuario_dia,
                        maat_cierre_manual_por_usuario_dia, num_lookup
                    )
            reg_hoy = registro_por_dia.get(reference_day, {})

            empleados_activos.append({
                'nombre': e['nombre'], 'puesto': e['puesto'], 'usuario': e['usuario'],
                'con_usuario': has_usuario(e['usuario']), 'descanso_oficial': e['descanso_oficial'],
                'horario_personal': e['horario_personal'], 'jornada': e.get('jornada'),
                'faltas_mes': faltas, 'asistencias_mes': asistencias, 'retardos_mes': retardos,
                # "Registra Pandape" / "Registra MAAT" = del día de corte (hoy) por default;
                # el detalle completo día por día vive en 'registro_por_dia'.
                'registra_pandape': reg_hoy.get('registra_pandape', False),
                'registra_maat': reg_hoy.get('registra_maat') if maat_cargado else None,
                'estatus_registro': reg_hoy.get('estatus_registro') if maat_cargado else None,
                'tienda_maat': reg_hoy.get('tienda_maat'),
                'se_movio_de_tienda': reg_hoy.get('se_movio_de_tienda', False),
                'tienda_maat_key': reg_hoy.get('tienda_maat_key'),   # clave de la tienda donde realmente registró (si se movió)
                'tienda_origen_key': key,              # clave de su tienda asignada (para reconstruir cobertura cruzada)
                'registro_por_dia': {str(d): v for d, v in registro_por_dia.items()},  # detalle día por día
            })

        store_results[key] = {
            'info': store,
            'activos_n': len(activos),
            'con_usuario_n': sum(1 for e in activos if has_usuario(e['usuario'])),
            'plantilla_autorizada': N,
            'vacantes_estructurales': max(0, N - len(activos)),
            'altas_mes': altas_mes, 'bajas_mes': bajas_mes, 'rotacion_pct': round(rotacion_pct, 1),
            'open': fmt_min(open_m), 'close': fmt_min(close_m),
            'dias': {str(k): v for k, v in day_metrics.items()},
            'hoy': hoy, 'ayer': ayer, 'reincidencia': reincidencia,
            'dias_rojo_mes': dias_rojo, 'promedio_cobertura_mes': promedio_mensual,
            'empleados_activos': empleados_activos,
            'bajas_detalle': [{'nombre': e['nombre'], 'fecha_baja': str(e['fecha_baja'])}
                               for e in emp_list if _es_del_mes(e['fecha_baja'], anio, mes)],
        }

    # Tiendas que aparecen en asistencia pero no en la base: solo importa si tienen
    # personal ACTIVO ahí (si todos son bajas/inactivos, no hay nada que corregir).
    activos_por_tienda_fantasma = {}
    for e in employees:
        if e['estatus'] == 'ACTIVO' and e['tienda_key'] not in stores:
            activos_por_tienda_fantasma.setdefault(e['tienda_key'], []).append(e['nombre'])
    no_en_base = [
        {'tienda_key': k, 'activos_n': len(v), 'nombres': v}
        for k, v in sorted(activos_por_tienda_fantasma.items())
    ]

    # Tiendas operando sin sublíder asignado
    sin_sublider = [
        {'key': k, 'tienda_nombre': s['tienda_nombre'], 'zona': s['zona'], 'region': s['region'],
         'ejecutiva': s['ejecutiva']}
        for k, s in stores.items() if s['estatus'] == 'OPERANDO' and not s.get('sublider')
    ]

    # Cobertura cruzada de MAAT: personas que están asignadas a una tienda pero que,
    # según MAAT, hoy registraron su asistencia en OTRA tienda — están cubriendo ahí.
    # Esto es clave para saber si una tienda con 0 activos propios registrando en MAAT
    # en realidad SÍ está cubierta porque alguien de otro lado llegó a cubrirla.
    cobertura_externa_maat = {}
    if maat_cargado:
        for sr in store_results.values():
            for e in sr['empleados_activos']:
                if e.get('se_movio_de_tienda') and e.get('registra_maat') and e.get('tienda_maat_key'):
                    destino = e['tienda_maat_key']
                    cobertura_externa_maat.setdefault(destino, []).append({
                        'nombre': e['nombre'],
                        'tienda_origen_key': e['tienda_origen_key'],
                        'tienda_origen_nombre': stores.get(e['tienda_origen_key'], {}).get('tienda_nombre') or e['tienda_origen_key'],
                    })

    # Personas que registran en MAAT pero NO existen en el archivo de asistencia
    # (ni activas ni de baja) — probablemente promotores nuevos que aún no se han
    # dado de alta en la asistencia, pero sí están trabajando según MAAT. Los
    # agregamos como "externos", ubicados en la tienda que dice MAAT (columna
    # 'Segundo punto de venta'), y marcados con 'es_externo_maat' para que se
    # note claramente que no vienen del archivo oficial de asistencia.
    externos_por_tienda = {}
    if maat_cargado:
        usuarios_conocidos = {norm(e['usuario']) for e in employees if e.get('usuario')}
        todos_usuarios_maat = set()
        for s in maat_usuarios_por_dia.values():
            todos_usuarios_maat |= s
        usuarios_externos = todos_usuarios_maat - usuarios_conocidos

        for u in sorted(usuarios_externos):
            registro_por_dia_u = {}
            for d in range(1, days_in_month + 1):
                registra_maat_d = u in maat_usuarios_por_dia.get(d, set())
                ubicacion_d = maat_ubicacion_por_usuario_dia.get((u, d))
                key_resuelta_d = _resolver_tienda_de_maat(ubicacion_d, num_lookup) if ubicacion_d else None
                registro_por_dia_u[d] = {'registra_maat': registra_maat_d, 'tienda_key_dia': key_resuelta_d}

            # Tienda "hogar": la de hoy si se pudo resolver; si no, la más frecuente del periodo.
            home_key = registro_por_dia_u.get(reference_day, {}).get('tienda_key_dia')
            if not home_key:
                conteo_tiendas = {}
                for v in registro_por_dia_u.values():
                    if v['tienda_key_dia']:
                        conteo_tiendas[v['tienda_key_dia']] = conteo_tiendas.get(v['tienda_key_dia'], 0) + 1
                if conteo_tiendas:
                    home_key = max(conteo_tiendas, key=conteo_tiendas.get)
            if not home_key or home_key not in store_results:
                continue  # no se pudo ubicar en ninguna tienda operando conocida

            reg_final = {}
            for d, v in registro_por_dia_u.items():
                se_movio = bool(v['tienda_key_dia'] and v['tienda_key_dia'] != home_key)
                tienda_maat_txt = None
                if se_movio:
                    nombre_resuelto = stores[v['tienda_key_dia']]['tienda_nombre'] or v['tienda_key_dia']
                    tienda_maat_txt = f"{nombre_resuelto} ({v['tienda_key_dia']})"
                reg_final[str(d)] = {
                    'registra_pandape': False, 'registra_maat': v['registra_maat'],
                    'estatus_registro': registro_categoria(False, v['registra_maat']),
                    'tienda_maat': tienda_maat_txt, 'tienda_maat_key': v['tienda_key_dia'] if se_movio else None,
                    'se_movio_de_tienda': se_movio,
                    'hora_entrada_pandape': None,
                    'hora_entrada_maat': maat_entrada_por_usuario_dia.get((u, d)) if v['registra_maat'] else None,
                    'hora_salida_pandape': None,
                    'hora_salida_maat': maat_salida_por_usuario_dia.get((u, d)) if v['registra_maat'] else None,
                    'cerro_jornada_manual': bool(maat_cierre_manual_por_usuario_dia.get((u, d))) if v['registra_maat'] else False,
                    'fuente_horario_programado': None, 'hora_inicio_programada': None, 'llego_tarde': False, 'minutos_tarde': None,
                    'salio_antes_de_horario': False, 'hora_fin_programada': None, 'minutos_antes_de_hora': None,
                }
            externos_por_tienda.setdefault(home_key, []).append({
                'nombre': f"{u} — externo (no está en asistencia)",
                'usuario': u, 'es_externo_maat': True,
                'registro_por_dia': reg_final,
            })

    for key in store_results:
        store_results[key]['externos_maat'] = externos_por_tienda.get(key, [])

    # Tiendas donde NINGÚN promotor activo está registrado en Pandape ni en MAAT
    # (solo tiene sentido si sí hay personal activo — si la tienda ya está vacía,
    # ese problema se refleja en otro lado del tablero). Si alguien de otra tienda
    # llegó a cubrir aquí según MAAT, ya no cuenta como "sin registro".
    tiendas_sin_registro = []
    if maat_cargado:
        for key, sr in store_results.items():
            activos = sr['empleados_activos']
            tiene_cobertura_externa = bool(cobertura_externa_maat.get(key))
            if activos and not tiene_cobertura_externa and all(e['estatus_registro'] == 'ALARMANTE' for e in activos):
                tiendas_sin_registro.append({
                    'key': key, 'tienda_nombre': sr['info']['tienda_nombre'], 'zona': sr['info']['zona'],
                    'region': sr['info']['region'], 'ejecutiva': sr['info']['ejecutiva'],
                    'activos_n': sr['activos_n'],
                })

    return {
        'meta': {
            'reference_day': reference_day, 'days_in_month': days_in_month,
            'total_stores_operando': len(store_results), 'no_en_base': no_en_base,
            'hora_corte': fmt_min(hora_corte_min) if hora_corte_min is not None else None,
            'maat_cargado': maat_cargado,
            'maat_dia_min': maat_dia_min, 'maat_dia_max': maat_dia_max,
            'maat_tiene_datos_hoy': maat_tiene_datos_hoy if maat_cargado else None,
            'diagnostico_tiendas': {
                'total_filas_en_archivo': stores_diag['total_filas'],
                'filas_sin_clave': stores_diag['filas_sin_key'],
                'claves_unicas': stores_diag['claves_unicas'],
                'claves_duplicadas': stores_diag['claves_duplicadas'],
                'conteo_por_estatus': estatus_counts,
            },
        },
        'stores': store_results,
        'cobertura_externa_maat': cobertura_externa_maat,
        'resumen_diario': {str(k): v for k, v in resumen_diario.items()},
        'sin_sublider': sin_sublider,
        'tiendas_sin_registro': tiendas_sin_registro,
    }
