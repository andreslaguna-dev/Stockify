import django.core.validators
import django.db.models.deletion
from decimal import Decimal
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventario', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='movimientoinventario',
            options={'ordering': ['-fecha'], 'verbose_name': 'Movimiento de Inventario', 'verbose_name_plural': 'Movimientos de Inventario (Kárdex)'},
        ),
        migrations.CreateModel(
            name='Temporada',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('codigo', models.CharField(blank=True, max_length=60, null=True, unique=True, verbose_name='Código Identificador')),
                ('nombre', models.CharField(max_length=150, verbose_name='Nombre del Evento o Temporada')),
                ('tipo', models.CharField(choices=[('RELIGIOSA', 'Religiosa / Turística (Semana Santa)'), ('FAMILIAR', 'Familiar / Celebración (Día de la Madre, Padre)'), ('SOCIAL', 'Social / Parejas (Amor y Amistad)'), ('VACACIONES', 'Temporada Vacacional (Año Nuevo, Mitad de Año, Diciembre)'), ('FESTIVAL_LOCAL', 'Festival o Feria Local (Reinado del Turismo Girardot)'), ('PUENTE', 'Puente Festivo Nacional (Ley Emiliani)'), ('OTRO', 'Temporada Personalizada')], default='PUENTE', max_length=20, verbose_name='Tipo de Temporada')),
                ('fecha_inicio', models.DateField(verbose_name='Inicio de Ventana de Demanda')),
                ('fecha_fin', models.DateField(verbose_name='Fin de Ventana de Demanda')),
                ('multiplicador_general', models.DecimalField(decimal_places=2, default=Decimal('1.80'), max_digits=4, validators=[django.core.validators.MinValueValidator(Decimal('0.10'))], verbose_name='Multiplicador Teórico Base')),
                ('prioridad', models.PositiveSmallIntegerField(choices=[(1, 'Alta (Prevalece si coincide con otra temporada)'), (2, 'Media'), (3, 'Baja')], default=2, verbose_name='Prioridad Jerárquica')),
                ('peso_historico', models.DecimalField(decimal_places=2, default=Decimal('0.70'), max_digits=3, validators=[django.core.validators.MinValueValidator(Decimal('0.00')), django.core.validators.MaxValueValidator(Decimal('1.00'))], verbose_name='Peso del Histórico Empírico vs Base Teórica')),
                ('es_recurrente', models.BooleanField(default=True, verbose_name='¿Se repite anualmente con reglas de calendario?')),
                ('descripcion', models.TextField(blank=True, null=True, verbose_name='Notas / Observaciones del Negocio')),
                ('activo', models.BooleanField(default=True, verbose_name='¿Activo?')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Temporada / Evento Comercial',
                'verbose_name_plural': 'Temporadas y Eventos Comerciales',
                'ordering': ['prioridad', 'fecha_inicio'],
            },
        ),
        migrations.CreateModel(
            name='ImpactoTemporadaCategoria',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('multiplicador', models.DecimalField(decimal_places=2, max_digits=4, validators=[django.core.validators.MinValueValidator(Decimal('0.05'))], verbose_name='Multiplicador Específico para esta Categoría (ej. 2.50 = +150%)')),
                ('categoria', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='impactos_temporada', to='inventario.categoria', verbose_name='Categoría Afectada')),
                ('temporada', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='impactos_categoria', to='inventario.temporada', verbose_name='Temporada')),
            ],
            options={
                'verbose_name': 'Impacto por Categoría en Temporada',
                'verbose_name_plural': 'Impactos por Categoría en Temporada',
                'unique_together': {('temporada', 'categoria')},
            },
        ),
    ]
