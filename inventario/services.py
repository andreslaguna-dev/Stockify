import math
from decimal import Decimal
import numpy as np
from scipy import stats
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from django.db.models.functions import TruncDate
from django.db.models import Sum
from .models import Producto, MovimientoInventario, Temporada, ImpactoTemporadaCategoria


def registrar_movimiento(
    producto: Producto, 
    tipo: str, 
    cantidad: Decimal, 
    costo_unitario: Decimal = None, 
    motivo: str = ""
) -> MovimientoInventario:
    """
    Registra un movimiento en el Kárdex de manera atómica (Transacción segura).
    Actualiza el stock físico del producto y guarda la trazabilidad.
    """
    if cantidad <= Decimal('0.00'):
        raise ValueError("La cantidad debe ser mayor a 0.")

    costo = costo_unitario if costo_unitario is not None else producto.costo_unitario

    # Transacción Atómica
    with transaction.atomic():
        prod = Producto.objects.select_for_update().get(pk=producto.pk)
        stock_anterior = prod.stock_actual

        if tipo == 'ENTRADA':
            prod.stock_actual += cantidad
            if costo_unitario is not None:
                prod.costo_unitario = costo_unitario
        elif tipo == 'SALIDA':
            if prod.stock_actual < cantidad:
                raise ValueError(
                    f"Stock insuficiente para {prod.nombre}. Stock actual: {prod.stock_actual}, solicitado: {cantidad}"
                )
            prod.stock_actual -= cantidad
        elif tipo == 'AJUSTE':
            prod.stock_actual = cantidad
        else:
            raise ValueError(f"Tipo de movimiento no válido: {tipo}")

        prod.save()

        movimiento = MovimientoInventario.objects.create(
            producto=prod,
            tipo=tipo,
            cantidad=cantidad,
            costo_unitario=costo,
            stock_anterior=stock_anterior,
            stock_resultante=prod.stock_actual,
            motivo=motivo
        )

        return movimiento


def obtener_temporada_activa(fecha=None) -> Temporada:
    """
    Retorna la temporada o evento comercial vigente para la fecha indicada
    (o la fecha actual si no se proporciona).
    Si coinciden múltiples eventos (ej: Puente Festivo y Día de la Madre),
    prevalece la de mayor prioridad jerárquica (prioridad 1 > 2 > 3).
    """
    if fecha is None:
        fecha = timezone.localdate()
    return Temporada.objects.filter(
        activo=True,
        fecha_inicio__lte=fecha,
        fecha_fin__gte=fecha
    ).order_by('prioridad', 'fecha_inicio').first()


def estimar_multiplicador_categoria(producto: Producto, temporada: Temporada) -> tuple[float, str]:
    """
    Calcula el multiplicador de demanda combinando:
    1. Multiplicador Teórico sugerido para la categoría (o general).
    2. Aprendizaje histórico empírico (si existen ventas registradas en temporadas pasadas del mismo tipo).
    3. Ponderación por Credibilidad Estadística (peso_historico).
    
    Retorna (multiplicador_final, detalle_explicativo).
    """
    if not temporada or not temporada.activo:
        return 1.0, "Día habitual (Sin factor estacional)"

    # Multiplicador Teórico Base
    impacto_cat = ImpactoTemporadaCategoria.objects.filter(
        temporada=temporada,
        categoria=producto.categoria
    ).first()

    multiplicador_teorico = float(impacto_cat.multiplicador if impacto_cat else temporada.multiplicador_general)

    # Buscar eventos históricos pasados del mismo tipo para aprender empíricamente
    hoy = timezone.localdate()
    temporadas_pasadas = Temporada.objects.filter(
        tipo=temporada.tipo,
        fecha_fin__lt=hoy
    )

    consumo_evento_acumulado = []
    for temp_pasada in temporadas_pasadas:
        salidas_temp = MovimientoInventario.objects.filter(
            producto=producto,
            tipo='SALIDA',
            fecha__date__gte=temp_pasada.fecha_inicio,
            fecha__date__lte=temp_pasada.fecha_fin
        ).annotate(dia=TruncDate('fecha')).values('dia').annotate(total=Sum('cantidad')).values_list('total', flat=True)

        consumo_evento_acumulado.extend([float(x) for x in salidas_temp])

    # Si hay al menos 3 días de histórico en eventos similares pasados, calculamos aprendizaje
    if len(consumo_evento_acumulado) >= 3:
        media_historica_evento = float(np.mean(consumo_evento_acumulado))
        
        # Consumo base promedio fuera de temporada (martes a jueves)
        salidas_base = MovimientoInventario.objects.filter(
            producto=producto,
            tipo='SALIDA'
        ).annotate(dia=TruncDate('fecha')).values('dia').annotate(total=Sum('cantidad')).values_list('total', flat=True)
        
        media_base_general = float(np.mean(salidas_base)) if salidas_base else 2.0
        if media_base_general > 0:
            multiplicador_observado = media_historica_evento / media_base_general
            peso = float(temporada.peso_historico)
            # Fórmula de Suavizado Ponderado (Credibilidad Bayesiana):
            multiplicador_ponderado = ((1.0 - peso) * multiplicador_teorico) + (peso * multiplicador_observado)
            multiplicador_final = max(1.0, round(multiplicador_ponderado, 2))
            detalle = f"{multiplicador_final}x (Aprendizaje: {multiplicador_observado:.2f}x observado, peso {int(peso*100)}%)"
            return multiplicador_final, detalle

    # Si aún no hay suficiente histórico acumulado, usamos la base teórica experta
    detalle = f"{multiplicador_teorico:.2f}x (Regla teórica recomendada)"
    return multiplicador_teorico, detalle



def calcular_metricas_inventario(
    producto: Producto, 
    temporada: Temporada = None,
    nivel_servicio: float = 0.95, 
    dias_historial: int = 30
) -> dict:
    """
    Calcula los parámetros estadísticos del producto basados en la demanda histórica real
    y aplica multiplicadores de temporada comercial (puentes festivos, fechas especiales):
    - Media diaria base y ajustada por temporada
    - Desviación estándar
    - Factor Z para el nivel de servicio
    - Colchón / Stock de Seguridad (SS)
    - Punto de Pedido / Reorden (ROP)
    - Stock Máximo sugerido
    - Sugerencia de compra en unidades reales
    - Probabilidad actual de rotura de stock
    """
    fecha_limite = timezone.now() - timedelta(days=dias_historial)

    # 1. Agrupar salidas por DÍA calendario para calcular consumo diario real
    consumos_diarios_qs = MovimientoInventario.objects.filter(
        producto=producto,
        tipo='SALIDA',
        fecha__gte=fecha_limite
    ).annotate(
        dia=TruncDate('fecha')
    ).values('dia').annotate(
        total_dia=Sum('cantidad')
    ).values_list('total_dia', flat=True)

    ventas_historicas = [float(v) for v in consumos_diarios_qs]

    if len(ventas_historicas) < 2:
        media_base = float(producto.stock_actual * Decimal('0.15')) if producto.stock_actual > 0 else 3.0
        desv_base = media_base * 0.25
    else:
        media_base = float(np.mean(ventas_historicas))
        desv_base = float(np.std(ventas_historicas, ddof=1)) if len(ventas_historicas) > 1 else media_base * 0.25

    # 2. Factor de Temporada / Festivo con Ventana y Aprendizaje Ponderado
    multiplicador = 1.0
    detalle_multiplicador = "Día estándar"
    nombre_temporada = "Estándar (Sin Evento)"

    if temporada and temporada.activo:
        nombre_temporada = temporada.nombre
        multiplicador, detalle_multiplicador = estimar_multiplicador_categoria(producto, temporada)

    # Demanda ajustada por la temporada comercial
    media_diaria = media_base * multiplicador
    # La variabilidad escala proporcionalmente a la volatilidad de la afluencia
    desviacion_diaria = desv_base * math.sqrt(multiplicador)


    L = max(1, producto.lead_time_dias)

    # 3. Factor Z (Inversa de la distribución normal estándar)
    z_score = float(stats.norm.ppf(nivel_servicio))

    # 4. Desviación estándar durante el tiempo de entrega: sigma_L = sigma * sqrt(L)
    sigma_lead_time = desviacion_diaria * math.sqrt(L)

    # 5. Colchón Mínimo / Stock de Seguridad (SS = Z * sigma * sqrt(L))
    stock_seguridad = math.ceil(z_score * sigma_lead_time)

    # 6. Demanda esperada durante el tiempo de entrega del proveedor
    demanda_esperada_lead_time = media_diaria * L

    # 7. Punto de Pedido / Reorden (ROP = Demanda_L + SS)
    punto_reorden = math.ceil(demanda_esperada_lead_time + stock_seguridad)

    # 8. Stock Máximo Recomendado (Punto de pedido + cobertura de 5 a 7 días)
    dias_cobertura = 4 if temporada else 7
    stock_maximo = math.ceil(punto_reorden + (media_diaria * dias_cobertura))

    # 9. Probabilidad de Desabastecimiento con el Stock Actual
    stock_actual_float = float(producto.stock_actual)
    if sigma_lead_time > 0:
        prob_desabastecimiento = float(1.0 - stats.norm.cdf(
            stock_actual_float, 
            loc=demanda_esperada_lead_time, 
            scale=sigma_lead_time
        ))
    else:
        prob_desabastecimiento = 1.0 if stock_actual_float < demanda_esperada_lead_time else 0.0

    # Estado del semáforo
    if stock_actual_float <= stock_seguridad:
        estado = "CRITICO"
    elif stock_actual_float <= punto_reorden:
        estado = "REORDENAR"
    elif stock_actual_float > stock_maximo:
        estado = "SOBRESTOCK"
    else:
        estado = "OPTIMO"

    # 10. Sugerencia de compra en unidades
    cantidad_sugerida = 0
    if estado in ['CRITICO', 'REORDENAR']:
        cantidad_sugerida = max(0, stock_maximo - math.floor(stock_actual_float))

    # 11. Presentación visual amigable para restaurante
    es_unidad = producto.unidad_medida == 'UND'
    if es_unidad:
        # En unidades enteras mostramos el aproximado comercial diario
        consumo_diario_display = f"~{math.ceil(media_diaria)} und/día"
    else:
        consumo_diario_display = f"{media_diaria:.1f} {producto.unidad_medida.lower()}/día"

    return {
        'producto_id': producto.id,
        'sku': producto.sku,
        'nombre': producto.nombre,
        'unidad_medida': producto.unidad_medida,
        'stock_actual': stock_actual_float,
        'lead_time_dias': L,
        'media_base': round(media_base, 2),
        'media_diaria': round(media_diaria, 2),
        'desviacion_diaria': round(desviacion_diaria, 2),
        'multiplicador_temporada': round(multiplicador, 2),
        'detalle_multiplicador': detalle_multiplicador,
        'nombre_temporada': nombre_temporada,

        'consumo_diario_display': consumo_diario_display,
        'nivel_servicio': nivel_servicio,
        'z_score': round(z_score, 3),
        'stock_seguridad': stock_seguridad,
        'punto_reorden': punto_reorden,
        'stock_maximo': stock_maximo,
        'cantidad_sugerida': cantidad_sugerida,
        'prob_desabastecimiento_pct': round(prob_desabastecimiento * 100, 1),
        'estado': estado,
    }

