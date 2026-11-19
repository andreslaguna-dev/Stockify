from django.contrib import admin
from .models import Categoria, Producto, MovimientoInventario, Temporada, ImpactoTemporadaCategoria


class ImpactoTemporadaCategoriaInline(admin.TabularInline):
    model = ImpactoTemporadaCategoria
    extra = 1


@admin.register(Temporada)
class TemporadaAdmin(admin.ModelAdmin):
    list_display = (
        'nombre', 
        'tipo', 
        'prioridad',
        'fecha_inicio', 
        'fecha_fin', 
        'multiplicador_general', 
        'peso_historico',
        'es_recurrente',
        'activo'
    )
    list_filter = ('tipo', 'prioridad', 'es_recurrente', 'activo')
    search_fields = ('nombre', 'codigo', 'descripcion')
    inlines = [ImpactoTemporadaCategoriaInline]
    ordering = ['prioridad', 'fecha_inicio']



@admin.register(ImpactoTemporadaCategoria)
class ImpactoTemporadaCategoriaAdmin(admin.ModelAdmin):
    list_display = ('temporada', 'categoria', 'multiplicador')
    list_filter = ('temporada', 'categoria')


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'activo', 'created_at')
    list_filter = ('activo',)
    search_fields = ('nombre',)


@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    list_display = (
        'sku', 
        'nombre', 
        'categoria', 
        'precio_venta', 
        'costo_unitario', 
        'stock_actual', 
        'lead_time_dias', 
        'activo'
    )
    list_filter = ('categoria', 'activo', 'unidad_medida')
    search_fields = ('sku', 'nombre')
    list_editable = ('precio_venta', 'activo')


@admin.register(MovimientoInventario)
class MovimientoInventarioAdmin(admin.ModelAdmin):
    list_display = (
        'fecha', 
        'producto', 
        'tipo', 
        'cantidad', 
        'costo_unitario', 
        'stock_anterior', 
        'stock_resultante'
    )
    list_filter = ('tipo', 'fecha')
    search_fields = ('producto__nombre', 'producto__sku', 'motivo')
    readonly_fields = ('fecha', 'stock_anterior', 'stock_resultante')

