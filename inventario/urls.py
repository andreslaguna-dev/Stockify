from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('movimiento/nuevo/', views.registrar_movimiento_view, name='registrar_movimiento'),
    path('kardex/exportar/', views.exportar_kardex_excel_view, name='exportar_kardex_excel'),
    path('kardex/exportar/<int:producto_id>/', views.exportar_kardex_excel_view, name='exportar_kardex_producto_excel'),
]
