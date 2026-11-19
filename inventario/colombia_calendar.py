"""
Módulo de cálculo de festivos y temporadas comerciales para Colombia (con foco en hostelería y turismo).
Implementa las reglas civiles colombianas:
- Ley Emiliani (Ley 51 de 1983): Traslado de festivos al lunes siguiente.
- Algoritmo de Computus (Meeus/Jones/Butcher) para el cálculo exacto de Semana Santa y fiestas pascuales.
- Reglas comerciales: Día de la Madre (2do domingo de mayo), Día del Padre (3er domingo de junio),
  Amor y Amistad (3er sábado de septiembre), Reinado Nacional del Turismo en Girardot (Puente de Octubre), etc.
"""

from datetime import date, timedelta
from decimal import Decimal


def calcular_pascua(year: int) -> date:
    """
    Calcula la fecha del Domingo de Resurrección (Pascua) para cualquier año
    utilizando el algoritmo computacional anónimo de Butcher / Meeus.
    """
    a = year % 19
    b = year // 100
    c = year % 100
    d = b // 4
    e = b % 4
    f = (b + 8) // 25
    g = (b - f + 1) // 3
    h = (19 * a + b - d - g + 15) % 30
    i = c // 4
    k = c % 4
    l = (32 + 2 * e + 2 * i - h - k) % 7
    m = (a + 11 * h + 22 * l) // 451
    mes = (h + l - 7 * m + 114) // 31
    dia = ((h + l - 7 * m + 114) % 31) + 1
    return date(year, mes, dia)


def trasladar_a_lunes_emiliani(fecha: date) -> date:
    """
    Aplica la Ley 51 de 1983 (Ley Emiliani): Si el festivo no cae en lunes,
    se traslada al siguiente lunes.
    """
    weekday = fecha.weekday()  # 0: Lunes, 6: Domingo
    if weekday == 0:
        return fecha
    dias_para_lunes = (7 - weekday) % 7
    if dias_para_lunes == 0:
        dias_para_lunes = 1
    return fecha + timedelta(days=dias_para_lunes)


def obtener_temporadas_colombia(year: int) -> list:
    """
    Genera el calendario anual completo de temporadas comerciales y festivos con ventanas
    de demanda realistas para restaurantes en Colombia (y específicamente la cuenca turística de Girardot).
    """
    temporadas = []
    pascua = calcular_pascua(year)

    # 1. Temporada de Año Nuevo y Reyes (Girardot / Turismo)
    # Afluencia masiva de turistas desde Bogotá para pasar vacaciones de inicio de año.
    temporadas.append({
        'codigo': f'ANO_NUEVO_{year}',
        'nombre': f'Año Nuevo y Reyes {year} (Temporada Alta)',
        'tipo': 'VACACIONES',
        'fecha_inicio': date(year, 1, 1),
        'fecha_fin': date(year, 1, 15),
        'multiplicador_general': Decimal('2.40'),
        'prioridad': 2,
        'descripcion': 'Temporada pico de inicio de año en Girardot. Ocupación hotelera máxima y turismo familiar.',
        'impactos': {
            'Pescados y Mariscos': Decimal('2.80'),
            'Carnes y Aves': Decimal('2.00'),
            'Acompañamientos y Guarniciones': Decimal('2.50'),
        }
    })

    # 2. Semana Santa (Ventana: Domingo de Ramos a Domingo de Resurrección)
    domingo_ramos = pascua - timedelta(days=7)
    domingo_resurreccion = pascua
    temporadas.append({
        'codigo': f'SEMANA_SANTA_{year}',
        'nombre': f'Semana Santa {year}',
        'tipo': 'RELIGIOSA',
        'fecha_inicio': domingo_ramos,
        'fecha_fin': domingo_resurreccion,
        'multiplicador_general': Decimal('2.50'),
        'prioridad': 1,  # Máxima prioridad
        'descripcion': 'Temporada religiosa y turística cumbre para pescaderías y restaurantes. Demanda récord de pescado.',
        'impactos': {
            'Pescados y Mariscos': Decimal('3.50'),  # Pescado se dispara hasta 3.5x
            'Carnes y Aves': Decimal('0.60'),       # La carne roja disminuye fuertemente
            'Acompañamientos y Guarniciones': Decimal('2.20'),
        }
    })

    # 3. Día de la Madre (Segundo domingo de mayo)
    # Ventana recomendada por hostelería: Jueves/Viernes antes hasta el Lunes posterior
    primer_dia_mayo = date(year, 5, 1)
    dias_hasta_domingo = (6 - primer_dia_mayo.weekday()) % 7
    primer_domingo_mayo = primer_dia_mayo + timedelta(days=dias_hasta_domingo)
    segundo_domingo_mayo = primer_domingo_mayo + timedelta(days=7)
    
    temporadas.append({
        'codigo': f'DIA_MADRE_{year}',
        'nombre': f'Día de la Madre {year}',
        'tipo': 'FAMILIAR',
        'fecha_inicio': segundo_domingo_mayo - timedelta(days=3),  # Desde el jueves/viernes de reservas
        'fecha_fin': segundo_domingo_mayo + timedelta(days=1),     # Lunes de resaca comercial
        'multiplicador_general': Decimal('2.80'),
        'prioridad': 1,
        'descripcion': 'El fin de semana de mayor facturación en restaurantes en Colombia. Pleno total en comedores.',
        'impactos': {
            'Pescados y Mariscos': Decimal('3.00'),
            'Carnes y Aves': Decimal('2.70'),
            'Acompañamientos y Guarniciones': Decimal('2.80'),
        }
    })

    # 4. Día del Padre (Tercer domingo de junio)
    # Ventana: Jueves a Lunes festivo habitual de junio
    primer_dia_junio = date(year, 6, 1)
    dias_hasta_domingo_jun = (6 - primer_dia_junio.weekday()) % 7
    primer_domingo_junio = primer_dia_junio + timedelta(days=dias_hasta_domingo_jun)
    tercer_domingo_junio = primer_domingo_junio + timedelta(days=14)

    temporadas.append({
        'codigo': f'DIA_PADRE_{year}',
        'nombre': f'Día del Padre {year}',
        'tipo': 'FAMILIAR',
        'fecha_inicio': tercer_domingo_junio - timedelta(days=2),
        'fecha_fin': tercer_domingo_junio + timedelta(days=1),
        'multiplicador_general': Decimal('2.00'),
        'prioridad': 2,
        'descripcion': 'Celebración familiar de alto consumo de carnes a la brasa, pescados y parrilladas.',
        'impactos': {
            'Pescados y Mariscos': Decimal('2.20'),
            'Carnes y Aves': Decimal('2.30'),
            'Acompañamientos y Guarniciones': Decimal('2.00'),
        }
    })

    # 5. Vacaciones de Mitad de Año (15 Junio - 15 Julio)
    temporadas.append({
        'codigo': f'VACACIONES_MITAD_{year}',
        'nombre': f'Vacaciones de Mitad de Año {year}',
        'tipo': 'VACACIONES',
        'fecha_inicio': date(year, 6, 15),
        'fecha_fin': date(year, 7, 15),
        'multiplicador_general': Decimal('1.70'),
        'prioridad': 3,
        'descripcion': 'Flujo constante entre semana y picos fuertes cada fin de semana por receso escolar y universitario.',
        'impactos': {
            'Pescados y Mariscos': Decimal('1.90'),
            'Carnes y Aves': Decimal('1.60'),
            'Acompañamientos y Guarniciones': Decimal('1.70'),
        }
    })

    # 6. Amor y Amistad (Tercer sábado de septiembre)
    # Ventana: Viernes a Domingo
    primer_dia_sept = date(year, 9, 1)
    dias_hasta_sabado = (5 - primer_dia_sept.weekday()) % 7
    primer_sabado_sept = primer_dia_sept + timedelta(days=dias_hasta_sabado)
    tercer_sabado_sept = primer_sabado_sept + timedelta(days=14)

    temporadas.append({
        'codigo': f'AMOR_AMISTAD_{year}',
        'nombre': f'Amor y Amistad {year}',
        'tipo': 'SOCIAL',
        'fecha_inicio': tercer_sabado_sept - timedelta(days=1),
        'fecha_fin': tercer_sabado_sept + timedelta(days=1),
        'multiplicador_general': Decimal('2.20'),
        'prioridad': 2,
        'descripcion': 'Salidas nocturnas, cenas de parejas, grupos de amigos y eventos corporativos de fin de semana.',
        'impactos': {
            'Pescados y Mariscos': Decimal('2.30'),
            'Carnes y Aves': Decimal('2.20'),
            'Acompañamientos y Guarniciones': Decimal('2.10'),
        }
    })

    # 7. Reinado Nacional del Turismo en Girardot (Puente de Octubre / Día de la Raza)
    # Se celebra tradicionalmente durante el puente festivo del 12 de octubre trasladado por Ley Emiliani
    dia_raza = trasladar_a_lunes_emiliani(date(year, 10, 12))
    viernes_fiestas = dia_raza - timedelta(days=3)
    temporadas.append({
        'codigo': f'REINADO_TURISMO_{year}',
        'nombre': f'Reinado Nacional del Turismo (Girardot) {year}',
        'tipo': 'FESTIVAL_LOCAL',
        'fecha_inicio': viernes_fiestas,
        'fecha_fin': dia_raza,
        'multiplicador_general': Decimal('2.70'),
        'prioridad': 1,
        'descripcion': 'Evento insignia de Girardot: Desfiles, conciertos y ríos de turistas. Demanda extrema.',
        'impactos': {
            'Pescados y Mariscos': Decimal('3.00'),
            'Carnes y Aves': Decimal('2.60'),
            'Acompañamientos y Guarniciones': Decimal('2.80'),
        }
    })

    # 8. Temporada Decembrina y Fin de Año (15 al 31 de Diciembre)
    temporadas.append({
        'codigo': f'FIN_ANO_{year}',
        'nombre': f'Temporada Decembrina y Fin de Año {year}',
        'tipo': 'VACACIONES',
        'fecha_inicio': date(year, 12, 15),
        'fecha_fin': date(year, 12, 31),
        'multiplicador_general': Decimal('2.50'),
        'prioridad': 2,
        'descripcion': 'Cenas de fin de año, vacaciones navideñas y alta ocupación turística en Girardot.',
        'impactos': {
            'Pescados y Mariscos': Decimal('2.70'),
            'Carnes y Aves': Decimal('2.50'),
            'Acompañamientos y Guarniciones': Decimal('2.60'),
        }
    })

    # 9. Puentes Festivos Típicos (Emiliani)
    # Por ejemplo San Pedro y San Pablo (finales de junio / inicios de julio)
    san_pedro = trasladar_a_lunes_emiliani(date(year, 6, 29))
    temporadas.append({
        'codigo': f'PUENTE_SAN_PEDRO_{year}',
        'nombre': f'Puente Festivo de San Pedro y San Pablo {year}',
        'tipo': 'PUENTE',
        'fecha_inicio': san_pedro - timedelta(days=3),  # Viernes
        'fecha_fin': san_pedro,                         # Lunes festivo
        'multiplicador_general': Decimal('2.10'),
        'prioridad': 3,
        'descripcion': 'Puente festivo típico de mitad de año con gran tráfico de turistas hacia Girardot.',
        'impactos': {
            'Pescados y Mariscos': Decimal('2.40'),
            'Carnes y Aves': Decimal('1.80'),
            'Acompañamientos y Guarniciones': Decimal('2.00'),
        }
    })

    return temporadas
