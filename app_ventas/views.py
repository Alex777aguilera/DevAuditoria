from django.db.models.expressions import Exists
from django.shortcuts import render,redirect
from django.http import HttpResponseRedirect,JsonResponse, HttpResponse
from django.urls import reverse
from django.db.models import Sum,Q
from django.contrib.auth.hashers import make_password
from datetime import date, datetime
from django.utils import timezone

from app_ventas.models import *
from django.contrib.auth import login as auth_login,logout,authenticate
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction,connections
#Correo
from django.core.mail import EmailMessage, send_mail
from Alejandro_Aguilera.settings import EMAIL_HOST_USER
#Librerias para PDF
from xhtml2pdf import pisa
from django.template.loader import get_template
from io import StringIO
from io import BytesIO

#####
import requests
import json
import base64

from rest_framework import serializers
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser

# Create your views here.

#Pagina principal de inicio

def inicio(request):
    try:
        cant_producto_precio = Productos.objects.all().aggregate(cant_total=Sum('precio'))
        precio_total_productos = cant_producto_precio['cant_total']

        cant_producto = Productos.objects.all().aggregate(totalP=Sum('cantidad'))
        cant_total_productos = cant_producto['totalP']
     
    except Productos.DoesNotExist:
        precio_total_productos = 0.1
        precio_total_productos = 0.1
        
    # consulta_fechas = Pedido.objects.filter(fecha_pedido__range=["2021-11-24", "2021-11-24"])#Consulta por rango de fechas, puee servir xd
    # # rango_precio_productos = Productos.objects.get(Q(precio > 100000)
    # print(consulta_fechas)
    
    ctx = {'precio':precio_total_productos,'totalP':cant_total_productos}
    if request.user.is_authenticated:
        return render(request,'inicio.html',ctx)
    else:
        return render(request,'error.html',ctx)

@login_required
def cerrar_sesion(request):
    logout(request)
    return HttpResponseRedirect(reverse('app_ventas:login'))

#Login
def login(request):
    mensaje=''
    if request.user.is_authenticated:
        return redirect('app_ventas:inicio')

    if request.method == 'POST':
        username = request.POST.get('usuario')
        contrasenia = request.POST.get('contrasenia')
        user = authenticate(username=username,password=contrasenia)
        if user is not None:
            if user.is_active:
                auth_login(request,user)
                return redirect('app_ventas:inicio')
            else:
                mensaje = 'USUARIO INACTIVO'
                return render(request,'login.html',{'mensaje':mensaje})
        else:
            mensaje = 'USUARIO O CONTRASEÑA INCORRECTO'
            return render(request,'login.html',{'mensaje':mensaje})

    return render(request,'login.html')

#Registro para el pedido
@login_required
def registrar_pedido(request):
    if request.user.is_authenticated:
        pedidos = Pedido.objects.all()
        productos = Productos.objects.all()
        clientes = Cliente.objects.all()
        ret_data,query_pedido,errores = {},{},{}

        if request.method == 'POST':
            
            ret_data['producto'] = request.POST.get('producto')
            ret_data['cliente'] = request.POST.get('cliente')
            ret_data['cantidad'] = request.POST.get('cantidad')
            
            # Producto
            if request.POST.get('producto') == '':
                errores['producto'] = "Debe ingresar el producto"

            # elif Productos.objects.filter(pk = int(request.POST.get("producto")).exists(): 
            # 	#Si el registro ya existe en la base de datos
            # 	errores['existe'] = 'ID ya Existente!!'
    
            else:
                query_pedido["producto"] = Productos.objects.get(pk=int(request.POST.get("producto")))

            
            # Ciente
            if request.POST.get('cliente') == '':
                errores['cliente'] = "Debe ingresar el cliente"
                
            else:
                query_pedido["cliente"] = Cliente.objects.get(pk=int(request.POST.get("cliente")))
            
            # Cantidad
            if request.POST.get('cantidad') == '' or request.POST.get('cantidad') == "0":
                errores['cantidad'] = "Debe ingresar la cantidad"
                
            else:
                query_pedido["cantidad"] = request.POST.get("cantidad")
                cantidad = int(request.POST.get("cantidad"))
            
            
            

            if not errores:

                try:
                    
                    query_pedido["vendedor"] = request.user
                    query_pedido["estado"] = Estado.objects.get(pk=1)
                    
                    
                    F_precio = Productos.objects.get(pk=int(request.POST.get("producto")))
                    precio = F_precio.precio
                    query_pedido["subtotal"] = float(cantidad*precio)
                    subtotal = query_pedido["subtotal"]
                    query_pedido["isv"] = float(subtotal*0.15)
                    query_pedido["total"] = float(subtotal) + float(subtotal*0.15)
                    ped = Pedido(**query_pedido)
                    ped.save()


                except Exception as e:
                    transaction.rollback()
                    errores['administrador'] = e
                    print (e)
                    ctx = {'pedidos':pedidos,'errores':errores,'ret_data':ret_data, 'clientes':clientes, 'productos':productos }

                    return render(request,'registrar_pedido.html',ctx)
                else:
                    transaction.commit()
                    return HttpResponseRedirect(reverse('app_ventas:registrar_pedido')+'?ok')
            else:
                ctx = {'pedidos':pedidos,'errores':errores,'ret_data':ret_data, 'clientes':clientes, 'productos':productos}
                return render(request,'registrar_pedido.html',ctx)
        else:
            ctx = {'pedidos':pedidos, 'clientes':clientes, 'productos':productos}
            return render(request,'registrar_pedido.html',ctx)
    else:
        return redirect('app_ventas:inicio')

#Aprobacion de pedidos

def aprobacion_pedidos(request):
    if request.user.is_authenticated:

        if request.user.is_superuser:
            PAprobados = Pedidos_Aprobados.objects.all()
            pedidos = Pedido.objects.exclude(estado = 2) #Realizamos una validacion para excluir y solo mostar los pedidos con estado "Aprobados"

            ret_data,query_pedidosA,errores = {},{},{}

            if request.method == 'POST':
                ret_data['pedido'] = request.POST.get('pedido')
                ret_data['descripcion_pedidos'] = request.POST.get('descripcion_pedidos')
                
                # pedido
                if request.POST.get('pedido') == '':
                    errores['pedido'] = "Debe ingresar el pedido"
                    
                else:
                    query_pedidosA["pedido"] = Pedido.objects.get(pk=int(request.POST.get("pedido")))
                
                #dscripcion
                query_pedidosA["descripcion_pedidos"] = request.POST.get("descripcion_pedidos")
                    

                if not errores:
                    try:
                        
                        query_pedidosA["encargado"] = request.user
                        Papronados = Pedidos_Aprobados(**query_pedidosA)
                        Papronados.save()
                        #Suma del total de productos del pedido
                        cant_producto_pedido = Pedido.objects.filter(pk=int(request.POST.get("pedido"))).aggregate(cant_total=Sum('cantidad'))
                        
                        pro =Pedido.objects.get(pk=int(request.POST.get("pedido")))#btengo un objeto que me peritira anej los diferentes campos del pedido
                        #Suma de la cantida del produco que se eligio para el pedido
                        cant_producto_total = Productos.objects.filter(pk=int(pro.producto.pk)).aggregate(cant_totalP=Sum('cantidad'))
                        #Disminucion de la cantidad de productos que se realizo el pedido y la cantidad restante.
                        resta_productos =int(cant_producto_total['cant_totalP']) -int(cant_producto_pedido['cant_total'])
                        

                        #Restar productos al hacer pedido
                        cantidad_productos = Productos.objects.filter(pk=int(pro.producto.pk)).update(
                                                                                cantidad =  resta_productos
                                                                                )

                        #Cambio de estado
                        nw_estado = Pedido.objects.filter(pk=int(request.POST.get("pedido"))).update(
                                                                                estado =  Estado.objects.get(pk=2)
                                                                                )

                    except Exception as e:
                        transaction.rollback()
                        errores['administrador'] = e
                        ctx = {'pedidos':pedidos,'PAprobados':PAprobados,'errores':errores,'ret_data':ret_data}

                        return render(request,'aprobacion_pedidos.html',ctx)
                    else:
                        transaction.commit()
                        return HttpResponseRedirect(reverse('app_ventas:aprobacion_pedidos'))
                else:
                    ctx = {'pedidos':pedidos,'PAprobados':PAprobados,'errores':errores,'ret_data':ret_data}
                    return render(request,'aprobacion_pedidos.html',ctx)
            else:
                ctx = {'pedidos':pedidos,'PAprobados':PAprobados}
                return render(request,'aprobacion_pedidos.html',ctx)
        else:
            return redirect('app_ventas:inicio')	
    else:
        return render(request,'error.html')

# Registrar Vendedor

def registrar_vendedor(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:

            ret_data,query_vendendor,errores = {},{},{}
            vendedores = Vendedor.objects.all()

            if request.method == 'POST':
                
                ret_data['nombres'] = request.POST.get('nombres')
                ret_data['apellidos'] = request.POST.get('apellidos')
                ret_data['direccion'] = request.POST.get('direccion')
                ret_data['telefono'] = request.POST.get('telefono')
                ret_data['cargo'] = request.POST.get('cargo')
                ret_data['correo'] = request.POST.get('correo')
                mail = request.POST.get('correo')
                lista_correo = []
                rango = 0
                username = ''
                password = ''

                # Nombres
                if request.POST.get('nombres') == '':
                    errores['nombres'] = "Debe ingresar el nombres"
                else:
                    query_vendendor["nombres"] = request.POST.get('nombres')

                
                # Apellido
                if request.POST.get('apellidos') == '':
                    errores['apellidos'] = "Debe ingresar el apellidos"
                    
                else:
                    query_vendendor["apellidos"] = request.POST.get('apellidos')
                
                # Direccion
                if request.POST.get('direccion') == '':
                    errores['direccion'] = "Debe ingresar la direccion"
                    
                else:
                    query_vendendor["direccion"] = request.POST.get('direccion')
                # Telefono
                if request.POST.get('telefono') == '':
                    errores['telefono'] = "Debe ingresar su telefono"
                    
                else:
                    query_vendendor["telefono"] = request.POST.get('telefono')
                    
                # Cargo
                if request.POST.get('cargo') == '':
                    errores['cargo'] = "Debe ingresar su cargo"
                    
                else:
                    query_vendendor["cargo"] = request.POST.get('cargo')
                    
                # Correo
                if request.POST.get('correo') == '':
                    errores['correo'] = "Debe ingresar su telefono"
                elif User.objects.filter(email = mail).exists():
                    errores['correo'] = "Correo ya existente"
                else:
                    query_vendendor["correo"] = request.POST.get('correo')
                    password = make_password('8')
                    print(password)
                    lista_correo.append(mail)
                    rango = mail.find('@') #Devulve la posicion donde esta el @
                    for x in range(0,rango):
                        username += mail[x]
                
            
                print(errores)
                if not errores:

                    try:
                        #Creación de usuario
                        User.objects.create_user(username, mail, password)
                        user = User.objects.last()
                        # guardar usuario par el vendendor 
                        query_vendendor['usuario'] = user
                        
                        ven = Vendedor(**query_vendendor)
                        ven.save()

                        #Envio de correo con los parametros del empleado
                        subject = '¡Un cordial saludo '+request.POST.get('nombres')+' '+request.POST.get('apellidos')
                        message = 'Su usuario es: ' + username + ', y password es: ' + password
                        recepient = mail
                        send_mail(subject, message, EMAIL_HOST_USER, [recepient], fail_silently = False)
                    except Exception as e:
                        transaction.rollback()
                        errores['administrador'] = e
                        print (e)
                        ctx = {'vendedores':vendedores,'errores':errores,'ret_data':ret_data }

                        return render(request,'registrar_vendedor.html',ctx)
                    else:
                        transaction.commit()
                        return HttpResponseRedirect(reverse('app_ventas:registrar_vendedor')+'?ok')
                else:
                    ctx = {'vendedores':vendedores,'errores':errores,'ret_data':ret_data}
                    return render(request,'registrar_vendedor.html',ctx)
            else:
                ctx = {'vendedores':vendedores}
                return render(request,'registrar_vendedor.html',ctx)
        else:
            return redirect('app_ventas:inicio')   
    else:
        return render(request,'error.html')


#Registro Cliente
def registrar_cliente(request):
    if request.user.is_authenticated:
        

        ret_data,query_cliente,errores = {},{},{}
        clientes = Cliente.objects.all()

        if request.method == 'POST':
            
            ret_data['nombres'] = request.POST.get('nombres')
            ret_data['apellidos'] = request.POST.get('apellidos')
            ret_data['direccion'] = request.POST.get('direccion')
            ret_data['telefono'] = request.POST.get('telefono')
            
            

            # Nombres
            if request.POST.get('nombres') == '':
                errores['nombres'] = "Debe ingresar el nombres"
            else:
                query_cliente["nombres"] = request.POST.get('nombres')

            # Apellido
            if request.POST.get('apellidos') == '':
                errores['apellidos'] = "Debe ingresar el apellidos"
                
            else:
                query_cliente["apellidos"] = request.POST.get('apellidos')
            
            # Direccion
            if request.POST.get('direccion') == '':
                errores['direccion'] = "Debe ingresar la direccion"
                
            else:
                query_cliente["direccion"] = request.POST.get('direccion')
            # Telefono
            if request.POST.get('telefono') == '':
                errores['telefono'] = "Debe ingresar su telefono"
                
            else:
                query_cliente["telefono"] = request.POST.get('telefono')
                
        
            print(errores)
            if not errores:

                try:
                    client = Cliente(**query_cliente)
                    client.save()

                except Exception as e:
                    transaction.rollback()
                    errores['administrador'] = e
                    print (e)
                    ctx = {'clientes':clientes,'errores':errores,'ret_data':ret_data }

                    return render(request,'registrar_cliente.html',ctx)
                else:
                    transaction.commit()
                    return HttpResponseRedirect(reverse('app_ventas:registrar_cliente')+'?ok')
            else:
                ctx = {'clientes':clientes,'errores':errores,'ret_data':ret_data}
                return render(request,'registrar_cliente.html',ctx)
        else:
            ctx = {'clientes':clientes}
            return render(request,'registrar_cliente.html',ctx)	 
    else:
        return render(request,'error.html')


#REPORTES PDF
@login_required
def PDF_PedidosA(request, id):
    if request.method == 'GET':
        
        PAprobados = Pedidos_Aprobados.objects.get(pk=id)
        
        Pedidos = Pedido.objects.get(pk=PAprobados.pedido.pk)
        
        productos = Productos.objects.get(pk=Pedidos.producto.pk)
        
        
        
        ctx = {'pedidosA':PAprobados,'producto':productos,'Pedidos':Pedidos}
        #ejecucion para generar el reporte pdf mostrando una previsualizacion en otra pestaña del navegador
        template = get_template('PDF_PedidosA.html')
        html = template.render(ctx)
        response = HttpResponse(content_type='application/pdf')
        pisaStatus = pisa.CreatePDF(html,dest=response)
        return response

        

@login_required
def PDF_PedidosVendedor(request, empleado):#Pedidos realizados por vendedor
    if request.method == 'GET':
        ctx = {}
        try:
            #.aggregate(cant_total=Sum('precio'))
            user = User.objects.get(pk = empleado)
            print(user.username)
            if Pedido.objects.filter(vendedor=user.username).exists():
                vendedor = Vendedor.objects.get(usuario=user.pk)
                pedidos = Pedido.objects.filter(vendedor=user.username,fecha_pedido__range=["2021-11-24", "2021-12-24"])
                print(vendedor.nombres)
                ctx = {'pedidos':pedidos,'vendedores':vendedor}
            else:
                ctx = {'pedidos':'No hay registros'}
        except Pedido.DoesNotExist:
            ctx = {'pedidos':'No hay registros'}

        
        
        #ejecucion para generar el reporte pdf mostrando una previsualizacion en otra pestaña del navegador
        template = get_template('PDF_PedidosVendedor.html')
        html = template.render(ctx)
        response = HttpResponse(content_type='application/pdf')
        pisaStatus = pisa.CreatePDF(html,dest=response)
        return response
#hola
def vista_grafica (request):
    return render(request,'vista_grafica.html')


#vista
class Apiproductos(APIView):
    ctx = {}
    def get(self, request, format=None):
        lista_prod = []
        lista_g = []
        if request.body:#Suponiendo que se enviara el id en el Json
            Data = json.loads(request.body)
            id_p = Data['ID'] #Id del tipo de producto a filtrar
            
            print(id_p)
            
            if Producto.objects.filter(pk=id_p).exists():
                p = Producto.objects.get(pk=id_p)
                g = Grupo.objects.all()

                lista_prod = [{'pk':p.pk, 'codigo':p.codigo, 'descripcion':p.descripcion, 'sub_grupo':p.sub_grupo, 'medida_mayor':p.medida_mayor, 'medida_menor':p.medida_menor, 'precio_mayoreo':p.precio_mayoreo, 'precio_detalle':p.precio_detalle, 'equivalencia':p.equivalencia, 'imagen':bytes(p.imagen), 'id_comentario':p.id_comentario.descripcion_comentario, 'id_categoria':p.id_categoria.descripcion_categoria, 'id_grupo':p.id_grupo.descripcion_grupo}]
                for g in Grupo.objects.all():
                    #lista_prod = [{'pk':p.pk, 'nombre_producto':p.nombre_producto, 'descripcion':p.descripcion, 'fecha_expira':p.fecha_expira, 'precio':p.precio, 'cantidad':p.cantidad, 'tipo_producto':p.tipo_producto.id, 'fecha_registro':p.fecha_registro, 'imagen':base64.b64encode(str(p.img_producto).encode('utf-8'))}]
                    
                    lista_g.append({'pk':g.pk, 'descripcion_grupo':g.descripcion_grupo})

                ctx = {'Id':'Encontrado','producto':lista_prod, 'grupo':lista_g}
                return Response(ctx)
            else:
                #productos = list(Producto.objects.all().values('pk','nombre_producto','descripcion','fecha_expira','precio','cantidad','tipo_producto','fecha_registro'))
                p = Producto.objects.all()
                g = Grupo.objects.all()

                for p in Producto.objects.all():
                    lista_prod.append({'pk':p.pk, 'codigo':p.codigo, 'descripcion':p.descripcion, 'sub_grupo':p.sub_grupo, 'medida_mayor':p.medida_mayor, 'medida_menor':p.medida_menor, 'precio_mayoreo':p.precio_mayoreo, 'precio_detalle':p.precio_detalle, 'equivalencia':p.equivalencia, 'imagen':bytes(p.imagen), 'id_comentario':p.id_comentario.descripcion_comentario,'id_categoria':p.id_categoria.descripcion_categoria,'id_grupo':p.id_grupo.descripcion_grupo})

                for g in Grupo.objects.all():
                    #lista_prod = [{'pk':p.pk, 'nombre_producto':p.nombre_producto, 'descripcion':p.descripcion, 'fecha_expira':p.fecha_expira, 'precio':p.precio, 'cantidad':p.cantidad, 'tipo_producto':p.tipo_producto.id, 'fecha_registro':p.fecha_registro, 'imagen':base64.b64encode(str(p.img_producto).encode('utf-8'))}]
                    
                    lista_g.append({'pk':g.pk, 'descripcion_grupo':g.descripcion_grupo})   

                ctx = {'Id':'No Encontrado','producto':lista_prod, 'grupo':lista_g}
                return Response(ctx)
        else:
            p = Producto.objects.all()
            g = Grupo.objects.all()

            for p in Producto.objects.all():
                lista_prod.append({'pk':p.pk, 'codigo':p.codigo, 'descripcion':p.descripcion, 'sub_grupo':p.sub_grupo, 'medida_mayor':p.medida_mayor, 'medida_menor':p.medida_menor, 'precio_mayoreo':p.precio_mayoreo, 'precio_detalle':p.precio_detalle, 'equivalencia':p.equivalencia, 'imagen':bytes(p.imagen), 'id_comentario':p.id_comentario.descripcion_comentario,'id_categoria':p.id_categoria.descripcion_categoria, 'id_grupo':p.id_grupo.descripcion_grupo})

            for g in Grupo.objects.all():
                    #lista_prod = [{'pk':p.pk, 'nombre_producto':p.nombre_producto, 'descripcion':p.descripcion, 'fecha_expira':p.fecha_expira, 'precio':p.precio, 'cantidad':p.cantidad, 'tipo_producto':p.tipo_producto.id, 'fecha_registro':p.fecha_registro, 'imagen':base64.b64encode(str(p.img_producto).encode('utf-8'))}]
                lista_g.append({'pk':g.pk, 'descripcion_grupo':g.descripcion_grupo})   

        if lista_prod:
            ctx = {'Id':'Id no solicitado','producto':lista_prod, 'grupo': lista_g}
            return Response(ctx)
        else:
            ctx = {'error','No hay Registros'}
            return Response(ctx)
            
##################################################################################
    
    def post(self, request, format=None):
    
        query_producto,errores, ctx = {},{},{}   
        if  request.method == 'POST':
            Data = json.loads(request.body)

            codigo = Data['codigo']
            descripcion = Data['descripcion']
            sub_grupo = Data['sub_grupo']
            medida_mayor = Data['medida_mayor']
            medida_menor = Data['medida_menor']
            precio_mayoreo = Data['precio_mayoreo']
            precio_detalle = Data['precio_detalle']
            equivalencia = Data['equivalencia']
            id_comentario = Data['id_comentario']
            id_categoria = Data['id_categoria']
            id_grupo = Data['id_grupo']
            imagen = Data['imagen']
            
            print (codigo, descripcion, sub_grupo, medida_mayor, medida_menor, precio_mayoreo, precio_detalle, equivalencia, id_comentario, id_categoria, id_grupo)
            print(imagen)

            type(imagen)
            # Codigo producto
            if request.POST.get('codigo') == '':
                errores['codigo'] = "Debe ingresar su Identidad"

            else:
                query_producto["codigo"] = codigo
            

            # Descripcion
            if request.POST.get('descripcion') == '':
                errores['descripcion'] = "Debe ingresar la descripcion"
            else:
                query_producto["descripcion"] = descripcion

            # Sub Grupo
            if request.POST.get('sub_grupo') == '':
                errores['sub_grupo'] = "Debe ingresar el Sub grupo"
            else:
                query_producto["sub_grupo"] = sub_grupo
            
            # medida_mayor
            if request.POST.get('medida_mayor') == '':
                errores['medida_mayor'] = "Debe ingresar la medida mayor"
            else:
                query_producto["medida_mayor"] = medida_mayor

            # medida_menor 
            if request.POST.get('medida_menor') == '':
                errores['medida_menor'] = "Debe ingresar la medida menor"
            else:
                query_producto["medida_menor"] = medida_menor

            # precio_mayoreo
            if request.POST.get('precio_mayoreo') == '':
                errores['precio_mayoreo'] = "Debe ingresar el precio de mayoreo"
            else:
                query_producto["precio_mayoreo"] = precio_mayoreo

            # precio_detalle 
            if request.POST.get('precio_detalle') == '':
                errores['precio_detalle'] = "Debe ingresar la precio detale"
            else:
                query_producto["precio_detalle"] = precio_detalle

            # equivalencia 
            if request.POST.get('equivalencia') == '':
                errores['equivalencia'] = "Debe ingresar la medida menor"
            else:
                query_producto["equivalencia"] = equivalencia


            # id_comentario
            if type(id_comentario) != int:
                errores['id_comentario'] = "El tipo de producto no es un entero"
            else:
                query_producto['id_comentario'] = Comentario.objects.get(pk=int(id_comentario))

            # id_categoria
            if type(id_categoria) != int:
                errores['id_categoria'] = "El tipo de producto no es un entero"
            else:
                query_producto['id_categoria'] = Categoria.objects.get(pk=int(id_categoria))

            # id_grupo
            if type(id_grupo) != int:
                errores['id_grupo'] = "El tipo de producto no es un entero"
            else:
                query_producto['id_grupo'] = Grupo.objects.get(pk=int(id_grupo))

            # img_producto
            if type(imagen) != str:
                errores['imagen'] = "La imagen del producto no es un binario"
            else:
                query_producto['imagen'] = bytes(imagen,'utf-8')

            print(errores)

            if not errores:
                prod = Producto(**query_producto)
                prod.save()
                ctx = {'Mensaje':'Producto agregado con exito'}
            else:
                ctx = {'Mensaje': errores}
            return Response(ctx)
        return Response(ctx)
