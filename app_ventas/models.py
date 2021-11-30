from django.db import models
from django.contrib.auth.models import User
from django.db.models.base import ModelStateFieldsCacheDescriptor
# Create your models here.

class Estado(models.Model):
    descripcion_estado = models.CharField(max_length=20, null = False,blank=False)
    
    def __str__(self):
        return "{}-{}".format(self.pk,self.descripcion_estado)

class Vendedor(models.Model):
    nombres = models.CharField(max_length=100, null = False,blank=False)
    apellidos = models.CharField(max_length=100, null = False,blank=False)
    fecha_registro = models.DateField(auto_now_add=True)
    direccion= models.CharField( max_length=100)
    correo = models.CharField(max_length=50)
    telefono = models.CharField( max_length=50)
    usuario = models.ForeignKey(User,on_delete=models.CASCADE, null=False,blank=False)
    cargo = models.CharField(max_length=100, null = False,blank=False)
    

    def __str__(self):
        return "{}-{}-{}".format(self.pk,self.nombres,self.apellidos,self.cargo)

class Cliente(models.Model):
    nombres = models.CharField(max_length=100, null = False,blank=False)
    apellidos = models.CharField(max_length=100, null = False,blank=False)
    fecha_registro = models.DateField(auto_now_add=True)
    direccion= models.CharField( max_length=100)
    telefono = models.CharField( max_length=50)
    fecha_registro = models.DateField( auto_now_add=True)


    def __str__(self):
        return "{}-{}-{}".format(self.pk,self.nombres,self.apellidos)

class Productos(models.Model):
    nombre_producto = models.CharField(max_length=100, null = False,blank=False)
    descripcion = models.CharField(max_length=200, null = False,blank=False)
    cantidad = models.IntegerField()
    precio = models.DecimalField( max_digits=20, decimal_places=2)
    fecha_registro = models.DateField( auto_now_add=True)

    def __str__(self):
        return "{}-{}-{}".format(self.pk,self.nombre_producto,self.precio)

class Pedido(models.Model):
    producto = models.ForeignKey(Productos,on_delete=models.CASCADE, null=False,blank=False)
    cliente = models.ForeignKey(Cliente,on_delete=models.CASCADE, null=False,blank=False)
    vendedor = models.CharField( max_length=50)
    estado = models.ForeignKey(Estado,on_delete=models.CASCADE, null=False,blank=False)
    cantidad = models.IntegerField()
    fecha_pedido = models.DateField( auto_now_add=True)
    isv = models.DecimalField( max_digits=20, decimal_places=2)
    subtotal = models.DecimalField( max_digits=20, decimal_places=2)
    total = models.DecimalField( max_digits=20, decimal_places=2)
    

    def __str__(self):
        return "{}-{}-{}-{}-{}".format(self.pk,self.producto.nombre_producto,self.producto.pk,self.cliente.nombres,self.estado)

class Pedidos_Aprobados(models.Model):
    descripcion_pedidos = models.CharField(max_length=100, null = False,blank=False)
    encargado = models.CharField(max_length=100, null = False,blank=False)
    pedido = models.ForeignKey(Pedido,on_delete=models.CASCADE, null=False,blank=False)
    fecha_aprobacion = models.DateField( auto_now_add=True)


    def __str__(self):
        return "{}-{}-{}-{}".format(self.pk,self.descripcion_pedidos,self.Pedido.pk,self.pedido.producto)

