from django.core.management.base import BaseCommand
from decimal import Decimal
from django.utils import timezone
from datetime import timedelta
import random
from inventario.models import Categoria, Producto, MovimientoInventario
from inventario.services import registrar_movimiento


class Command(BaseCommand):
    help = 'Puebla la base de datos con los productos y existencias reales de la hoja de restaurante'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Limpiando base de datos anterior...'))
        MovimientoInventario.objects.all().delete()
        Producto.objects.all().delete()
        Categoria.objects.all().delete()

        # Categorías del restaurante
        cat_pescados = Categoria.objects.create(
            nombre='Pescados y Mariscos',
            descripcion='Pescados frescos de río y mar, enteros y en porciones'
        )
        cat_carnes = Categoria.objects.create(
            nombre='Carnes y Aves',
            descripcion='Cortes de res, pechugas de pollo y empanizados'
        )
        cat_guarniciones = Categoria.objects.create(
            nombre='Acompañamientos y Guarniciones',
            descripcion='Papas, yucas y complementos para platos principales'
        )

        # 17 Productos extraídos de la hoja de control físico (Domingo 23)
        productos_data = [
            ('Mojarra Grande', cat_pescados, 'PES-001', Decimal('54.00'), 'UND', Decimal('18000.00'), Decimal('32000.00'), 2),
            ('Mojarra Pequeña', cat_pescados, 'PES-002', Decimal('45.00'), 'UND', Decimal('14000.00'), Decimal('25000.00'), 2),
            ('Cachama Grande', cat_pescados, 'PES-003', Decimal('8.00'), 'UND', Decimal('16000.00'), Decimal('28000.00'), 2),
            ('Cachama Pequeña', cat_pescados, 'PES-004', Decimal('7.00'), 'UND', Decimal('12000.00'), Decimal('22000.00'), 2),
            ('Róbalo', cat_pescados, 'PES-005', Decimal('12.00'), 'UND', Decimal('22000.00'), Decimal('38000.00'), 3),
            ('Pez Temporada', cat_pescados, 'PES-006', Decimal('37.00'), 'UND', Decimal('15000.00'), Decimal('28000.00'), 2),
            ('Bagre', cat_pescados, 'PES-007', Decimal('9.00'), 'UND', Decimal('18000.00'), Decimal('30000.00'), 2),
            ('Trucha', cat_pescados, 'PES-008', Decimal('6.00'), 'UND', Decimal('19000.00'), Decimal('34000.00'), 3),
            ('Pechuga Grande', cat_carnes, 'CAR-001', Decimal('5.00'), 'UND', Decimal('15000.00'), Decimal('26000.00'), 2),
            ('Pechuga Pequeña', cat_carnes, 'CAR-002', Decimal('7.00'), 'UND', Decimal('11000.00'), Decimal('20000.00'), 2),
            ('Churrasco Grande', cat_carnes, 'CAR-003', Decimal('9.00'), 'UND', Decimal('24000.00'), Decimal('42000.00'), 2),
            ('Churrasco Pequeño', cat_carnes, 'CAR-004', Decimal('7.00'), 'UND', Decimal('17000.00'), Decimal('30000.00'), 2),
            ('Nuggets', cat_carnes, 'CAR-005', Decimal('111.00'), 'UND', Decimal('600.00'), Decimal('1200.00'), 3),
            ('Papa Frita', cat_guarniciones, 'GUA-001', Decimal('1.25'), 'PAQ', Decimal('35000.00'), Decimal('60000.00'), 2),
            ('Yuca Frita', cat_guarniciones, 'GUA-002', Decimal('7.00'), 'PAQ', Decimal('15000.00'), Decimal('25000.00'), 2),
            ('Cachama de Consomé', cat_pescados, 'PES-009', Decimal('0.00'), 'UND', Decimal('8000.00'), Decimal('15000.00'), 2),
            ('Cabeza de Mojarra', cat_pescados, 'PES-010', Decimal('0.00'), 'UND', Decimal('4000.00'), Decimal('8000.00'), 2),
        ]

        random.seed(42)

        for nombre, cat, sku, stock_inicial, unidad, costo, precio, lead_time in productos_data:
            p = Producto.objects.create(
                nombre=nombre,
                categoria=cat,
                sku=sku,
                stock_actual=Decimal('0.00'),
                unidad_medida=unidad,
                costo_unitario=costo,
                precio_venta=precio,
                lead_time_dias=lead_time
            )

            # Entrada del inventario físico inicial (Kárdex trazable)
            if stock_inicial > Decimal('0.00'):
                registrar_movimiento(
                    producto=p,
                    tipo='ENTRADA',
                    cantidad=stock_inicial,
                    costo_unitario=costo,
                    motivo='Inventario Físico Inicial - Hoja de Control Domingo 23'
                )

            # Ventas históricas para alimentar las fórmulas estocásticas de SciPy (ROP y SS)
            media_aprox = max(2.0, float(stock_inicial) * 0.25)
            for i in range(14, 0, -1):
                fecha_hist = timezone.now() - timedelta(days=i)
                salida_cant = max(1, int(random.gauss(media_aprox, media_aprox * 0.25)))
                mov = MovimientoInventario.objects.create(
                    producto=p,
                    tipo='SALIDA',
                    cantidad=Decimal(str(salida_cant)),
                    costo_unitario=costo,
                    stock_anterior=p.stock_actual,
                    stock_resultante=p.stock_actual,
                    motivo=f'Venta POS Restaurante - Día -{i}'
                )
                MovimientoInventario.objects.filter(pk=mov.pk).update(fecha=fecha_hist)

        self.stdout.write(self.style.SUCCESS(f'¡Éxito! Se cargaron los {Producto.objects.count()} productos reales del restaurante.'))
