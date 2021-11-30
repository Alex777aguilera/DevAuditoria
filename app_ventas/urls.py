from django.urls import path


from . import views

app_name = 'app_ventas'

urlpatterns = [
 path('', views.login, name='login'),	
 path('cerrar_sesion', views.cerrar_sesion, name='cerrar_sesion'),	
 path('inicio', views.inicio, name='inicio'),
 path('vista/registrar_pedido', views.registrar_pedido, name='registrar_pedido'),	
 path('vista/aprobacion_pedidos', views.aprobacion_pedidos, name='aprobacion_pedidos'),	
 path('vista/registrar_vendedor', views.registrar_vendedor, name='registrar_vendedor'),	
 path('vista/registrar_cliente', views.registrar_cliente, name='registrar_cliente'),	

 #Reportes
 path('PDF_PedidosA/<int:id>/', views.PDF_PedidosA, name='PDF_PedidosA'),	
 path('PDF_Pedidos/Vendedor/<int:empleado>/', views.PDF_PedidosVendedor, name='PDF_PedidosVendedor'),	
]