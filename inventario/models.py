from django.db import models
from django.core.validators import MinValueValidator
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
        return f"{self.tipo} - {self.producto.nombre} ({self.cantidad}) [{self.fecha.strftime('%Y-%m-%d %H:%M')}]"

