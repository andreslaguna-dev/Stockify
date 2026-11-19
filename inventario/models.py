from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

class Categoria(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre de la Categoría")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    activo = models.BooleanField(default=True, verbose_name="¿Activo?")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Producto(models.Model):
    UNIDADES_MEDIDA = [
        ('UND', 'Unidad'),
        ('KG', 'Kilogramo'),
        ('LT', 'Litro'),
        ('MTR', 'Metro'),
        ('PAQ', 'Paquete / Caja'),
    ]

    sku = models.CharField(max_length=50, unique=True, verbose_name="SKU / Código de Barras")
    nombre = models.CharField(max_length=200, verbose_name="Nombre del Producto")
    categoria = models.ForeignKey(
        Categoria, 
        on_delete=models.PROTECT, 
        related_name='productos', 
        verbose_name="Categoría"
    )
    unidad_medida = models.CharField(
        max_length=5, 
        choices=UNIDADES_MEDIDA, 
        default='UND', 
        verbose_name="Unidad de Medida"
    )
    costo_unitario = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Costo de Compra (Unitario)"
    )
    precio_venta = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.00'))],
        verbose_name="Precio de Venta"
    )
    stock_actual = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=Decimal('0.00'),
        verbose_name="Stock Físico Actual"
    )
    # Parámetro Estadístico para Punto de Reorden (ROP) y Stock de Seguridad
    lead_time_dias = models.PositiveIntegerField(
        default=3, 
        verbose_name="Tiempo de Entrega del Proveedor (Días)"
    )
    activo = models.BooleanField(default=True, verbose_name="¿Disponible para Venta?")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        ordering = ['nombre']

    def __str__(self):
        return f"{self.sku} - {self.nombre}"


class MovimientoInventario(models.Model):
    TIPO_MOVIMIENTO = [
        ('ENTRADA', 'Entrada (Compra / Devolución cliente)'),
        ('SALIDA', 'Salida (Venta / Merma)'),
        ('AJUSTE', 'Ajuste de Inventario'),
    ]

    producto = models.ForeignKey(
        Producto, 
        on_delete=models.CASCADE, 
        related_name='movimientos', 
        verbose_name="Producto"
    )
    tipo = models.CharField(max_length=10, choices=TIPO_MOVIMIENTO, verbose_name="Tipo de Movimiento")
    cantidad = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.01'))],
        verbose_name="Cantidad"
    )
    costo_unitario = models.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        verbose_name="Costo Unitario del Movimiento"
    )
    stock_anterior = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Stock Previo"
    )
    stock_resultante = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        verbose_name="Stock Resultante (Saldo)"
    )
    motivo = models.CharField(max_length=255, blank=True, null=True, verbose_name="Motivo / Documento de Referencia")
    fecha = models.DateTimeField(auto_now_add=True, verbose_name="Fecha del Movimiento")

    class Meta:
        verbose_name = "Movimiento de Inventario"
        verbose_name_plural = "Movimientos de Inventario (Kárdex)"
        ordering = ['-fecha']

    def __str__(self):
        return f"{self.tipo} - {self.producto.nombre} ({self.cantidad}) - {self.fecha.strftime('%d/%m/%Y %H:%M')}"


class Temporada(models.Model):
    """
    Configura temporadas comerciales, puentes festivos y fechas especiales
    (Día de la Madre, Semana Santa, Amor y Amistad, Reinado del Turismo, etc.).
    Implementa ventanas de demanda, prioridad por coincidencia y aprendizaje ponderado.
    """
    TIPOS = [
        ('RELIGIOSA', 'Religiosa / Turística (Semana Santa)'),
        ('FAMILIAR', 'Familiar / Celebración (Día de la Madre, Padre)'),
        ('SOCIAL', 'Social / Parejas (Amor y Amistad)'),
        ('VACACIONES', 'Temporada Vacacional (Año Nuevo, Mitad de Año, Diciembre)'),
        ('FESTIVAL_LOCAL', 'Festival o Feria Local (Reinado del Turismo Girardot)'),
        ('PUENTE', 'Puente Festivo Nacional (Ley Emiliani)'),
        ('OTRO', 'Temporada Personalizada'),
    ]

    PRIORIDADES = [
        (1, 'Alta (Prevalece si coincide con otra temporada)'),
        (2, 'Media'),
        (3, 'Baja'),
    ]

    codigo = models.CharField(max_length=60, blank=True, null=True, unique=True, verbose_name="Código Identificador (ej. SEMANA_SANTA_2026)")
    nombre = models.CharField(max_length=150, verbose_name="Nombre del Evento o Temporada")
    tipo = models.CharField(max_length=20, choices=TIPOS, default='PUENTE', verbose_name="Tipo de Temporada")
    fecha_inicio = models.DateField(verbose_name="Inicio de Ventana de Demanda")
    fecha_fin = models.DateField(verbose_name="Fin de Ventana de Demanda")
    multiplicador_general = models.DecimalField(
        max_digits=4, 
        decimal_places=2, 
        default=Decimal('1.80'),
        validators=[MinValueValidator(Decimal('0.10'))],
        verbose_name="Multiplicador Teórico Base (ej. 2.40 = +140% demanda)"
    )
    prioridad = models.PositiveSmallIntegerField(
        choices=PRIORIDADES,
        default=2,
        verbose_name="Prioridad Jerárquica"
    )
    peso_historico = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal('0.70'),
        validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('1.00'))],
        verbose_name="Peso del Histórico Empírico vs Base Teórica (0.0 a 1.0)"
    )
    es_recurrente = models.BooleanField(
        default=True, 
        verbose_name="¿Se repite anualmente con reglas de calendario?"
    )
    descripcion = models.TextField(blank=True, null=True, verbose_name="Notas / Observaciones del Negocio")
    activo = models.BooleanField(default=True, verbose_name="¿Activo?")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Temporada / Evento Comercial"
        verbose_name_plural = "Temporadas y Eventos Comerciales"
        ordering = ['prioridad', 'fecha_inicio']

    def __str__(self):
        return f"{self.nombre} ({self.fecha_inicio.strftime('%d/%m')} al {self.fecha_fin.strftime('%d/%m/%Y')}) - {self.multiplicador_general}x (Prioridad {self.prioridad})"

    def esta_vigente_en(self, fecha_consulta=None):
        from django.utils import timezone
        if fecha_consulta is None:
            fecha_consulta = timezone.localdate()
        return self.fecha_inicio <= fecha_consulta <= self.fecha_fin



class ImpactoTemporadaCategoria(models.Model):
    """
    Permite afinar el multiplicador por categoría específica en una temporada.
    Ejemplo: En Semana Santa, Pescados sube a 2.5x pero Carnes baja a 0.6x.
    """
    temporada = models.ForeignKey(
        Temporada, 
        on_delete=models.CASCADE, 
        related_name='impactos_categoria',
        verbose_name="Temporada"
    )
    categoria = models.ForeignKey(
        Categoria, 
        on_delete=models.CASCADE, 
        related_name='impactos_temporada',
        verbose_name="Categoría Afectada"
    )
    multiplicador = models.DecimalField(
        max_digits=4, 
        decimal_places=2, 
        validators=[MinValueValidator(Decimal('0.05'))],
        verbose_name="Multiplicador Específico para esta Categoría (ej. 2.50 = +150%)"
    )

    class Meta:
        verbose_name = "Impacto por Categoría en Temporada"
        verbose_name_plural = "Impactos por Categoría en Temporada"
        unique_together = ('temporada', 'categoria')

    def __str__(self):
        return f"{self.temporada.nombre} -> {self.categoria.nombre}: {self.multiplicador}x"


