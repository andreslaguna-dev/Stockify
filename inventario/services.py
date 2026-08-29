import math
from decimal import Decimal
import numpy as np
from scipy import stats
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from .models import Producto, MovimientoInventario


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

    # Transacción Atómica (Equivalente a DB::transaction en Laravel)
    with transaction.atomic():
        # Bloqueamos la fila del producto para evitar condiciones de carrera (Concurrency lock)
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


def calcular_metricas_inventario(producto: Producto, nivel_servicio: float = 0.95, dias_historial: int = 30) -> dict:
    """
    Calcula los parámetros estadísticos del producto basados en la demanda histórica:
    - Media diaria (mu)
    - Desviación estándar diaria (sigma)
    - Factor Z para el nivel de servicio
    - Stock de Seguridad (SS)
    - Punto de Reorden (ROP)
    - Stock Máximo sugerido
    - Probabilidad actual de rotura de stock
    """
    fecha_limite = timezone.now() - timedelta(days=dias_historial)

    salidas = MovimientoInventario.objects.filter(
        producto=producto,
        tipo='SALIDA',
        fecha__gte=fecha_limite
    ).values_list('cantidad', flat=True)

    ventas_historicas = [float(v) for v in salidas]

    if len(ventas_historicas) < 3:
        media_diaria = float(producto.stock_actual * Decimal('0.1')) if producto.stock_actual > 0 else 5.0
        desviacion_diaria = media_diaria * 0.3
    else:
        media_diaria = float(np.mean(ventas_historicas))
        desviacion_diaria = float(np.std(ventas_historicas, ddof=1))

    L = max(1, producto.lead_time_dias)

    # 1. Factor Z (Inversa de la distribución normal estándar)
    z_score = float(stats.norm.ppf(nivel_servicio))

    # 2. Desviación estándar durante el tiempo de entrega: sigma_L = sigma * sqrt(L)
    sigma_lead_time = desviacion_diaria * math.sqrt(L)

    # 3. Stock de Seguridad: SS = Z * sigma * sqrt(L)
    stock_seguridad = math.ceil(z_score * sigma_lead_time)

    # 4. Demanda esperada durante el tiempo de entrega: D_L = mu * L
    demanda_esperada_lead_time = media_diaria * L

    # 5. Punto de Reorden: ROP = (mu * L) + SS
    punto_reorden = math.ceil(demanda_esperada_lead_time + stock_seguridad)

    # 6. Stock Máximo Recomendado (ROP + Cobertura de ciclo de 7 días)
    stock_maximo = math.ceil(punto_reorden + (media_diaria * 7))

    # 7. Probabilidad de Desabastecimiento con el Stock Actual
    stock_actual_float = float(producto.stock_actual)
    if sigma_lead_time > 0:
        prob_desabastecimiento = float(1.0 - stats.norm.cdf(
            stock_actual_float, 
            loc=demanda_esperada_lead_time, 
            scale=sigma_lead_time
        ))
    else:
        prob_desabastecimiento = 1.0 if stock_actual_float < demanda_esperada_lead_time else 0.0

    # Estado del inventario para alertas tipo semáforo
    if stock_actual_float <= stock_seguridad:
        estado = "CRITICO"
    elif stock_actual_float <= punto_reorden:
        estado = "REORDENAR"
    elif stock_actual_float > stock_maximo:
        estado = "SOBRESTOCK"
    else:
        estado = "OPTIMO"

    return {
        'producto_id': producto.id,
        'sku': producto.sku,
        'nombre': producto.nombre,
        'stock_actual': stock_actual_float,
        'lead_time_dias': L,
        'media_diaria': round(media_diaria, 2),
        'desviacion_diaria': round(desviacion_diaria, 2),
        'nivel_servicio': nivel_servicio,
        'z_score': round(z_score, 3),
        'stock_seguridad': stock_seguridad,
        'punto_reorden': punto_reorden,
        'stock_maximo': stock_maximo,
        'prob_desabastecimiento_pct': round(prob_desabastecimiento * 100, 2),
        'estado': estado,
    }
