import datetime
import os
import re

from Tools.scripts.pysource import print_debug
from django.shortcuts import render, redirect
import uuid
from django.db import connection
from datetime import datetime
from django.shortcuts import render, redirect
from django.core.files.base import ContentFile
from django.shortcuts import render
from django.templatetags.static import static
import requests
from database.models import Customer, Vendor, DeliveryP, Favorite,RestaurantTag, Tag, Item, Restaurant, Order, User, Inbox, VideoFrame # type: ignore
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from channels.layers import get_channel_layer # type: ignore
from asgiref.sync import async_to_sync
import json
from geopy.geocoders import Nominatim # type: ignore
from geopy.exc import GeocoderTimedOut, GeocoderServiceError # type: ignore

from .form import UserRegistrationForm, UserLoginForm
from django.utils import timezone

# Create your views here.

def give_exp_func():
    data = [
            {
                "id": 1,
                "name": "Luigi’s Pizzeria",
                "tags": ["Italian", "Pizza", "Pasta"],
                "description": "Authentic Italian cuisine with wood-fired pizzas and homemade pasta.",
                "menu": [
                    {"name": "Margherita Pizza", "price": 8.99, "pic": static("assets/ex.jpg")},
                    {"name": "Spaghetti Bolognese", "price": 10.50, "pic": static("assets/ex2.jpg")},
                ],
                "address": "eqwdsad",
                "img": static("assets/ex.jpg"),
            },
            {
                "id": 2,
                "name": "Dragon Wok",
                "tags": ["Chinese", "Noodles", "Spicy"],
                "description": "Spicy Sichuan and Cantonese dishes.",
                "menu": [
                    {"name": "Kung Pao Chicken", "price": 9.99, "pic": static("assets/ex.jpg")},
                    {"name": "Beef Chow Mein", "price": 11.25, "pic": static("assets/ex2.jpg")},
                ],
                "address": "34435",
                "img": static("assets/ex2.jpg"),
            },
        ]
    return data



def front(request):
    data = give_exp_func()
    #test_user = DeliveryP.objects.first()
    #test_user = Customer.objects.first()
    # test_user = User.objects.get(user_id = user_id)
    #test_user= Vendor.objects.first()
    #user = request.user

    # if isinstance(test_user, Customer):
    #     role = 'customer'
    # elif isinstance(test_user, Vendor):
    #     role = 'vendor'
    # elif isinstance(test_user, DeliveryP):
    #     role = 'delivery'
    test_user = None
    user_id = request.session.get('user_id')
    role = request.session.get('role')
    if role == 'customer': test_user = Customer.objects.get(user_ptr_id = user_id)
    elif role == 'vendor': test_user = Vendor.objects.get(user_ptr_id = user_id)
    elif role == 'delivery': test_user = DeliveryP.objects.get(user_ptr_id = user_id)
    else: print(f"in orderpage/view.py ,role error : {role}")

    messages = Inbox.objects.raw("SELECT * FROM inbox WHERE user_id = %s", [test_user.pk])
    msg = []
    for m in messages:
        msg.append({
            "message": m.message,
            "timestamp": m.timestamp
        })
    if role == 'delivery':
        avaliable = Order.objects.raw("SELECT * FROM 'order' WHERE status = 'not started'")
        order_queue = []
        for o in avaliable:

            order_queue.append({
                "id": o.id,
                "created": o.created_at,
                "customer": o.user_id,
                "restaurant": o.restaurant_id,
         
              
            })
        return render(request, "index.html", {'Role': role, 'Username': test_user.name, 'userid': test_user.user_id, 'Orders':order_queue, 'msg': msg})
    
    if role == 'vendor':
        tags = Tag.objects.raw("SELECT * FROM tag")
        T_tags = []
        for t in tags:
            T_tags.append({
                "id":t.id,
                "Name":t.name,
            })
        if test_user.store_id is None:
            return render(request, "index.html", {'Role': role, 'Username': test_user.name, 'userid': test_user.user_id, 'msg': msg, "NoRes": True, "Tags": T_tags})
        pending = Order.objects.raw("SELECT * FROM 'order' WHERE restaurant_id = %s and status = 'pending'", [test_user.store_id])
        order_inc = []
        for o in pending:
            Customer_obj = User.objects.get(user_id=o.user_id)

            itemId = o.items.split(",")
            itms = []
            for i in itemId:
                item = list(Item.objects.raw("SELECT * FROM item WHERE id = %s", [i]))[0]
                itms.append({
                    "name": item.name,
                    "price":item.price,
                    "desc": item.desc,
                }) 
            order_inc.append({
                "id": o.id,
                "items": itms,
                'price': o.price,
                "created": o.created_at,
                "customer": Customer_obj.name,
                "delivery": o.delivery_person_id,
            })
        return render(request, "index.html", {'Role': role, 'Username': test_user.name, 'userid': test_user.user_id, 'Orders':order_inc, 'msg': msg, "NoRes": False, "Tags": T_tags})
    
    if role == 'customer':
       restaurants  = Restaurant.objects.raw("SELECT * FROM restaurant")
       data = []
       for r in restaurants:
           data.append({
               "id": r.Rid,
                "name": r.name,
                "address": r.address,
                "img": r.picture,
           })
       return render(request, "index.html", {'Test':data, 'Role': role, 'Username': test_user.name, 'userid': test_user.user_id, 'msg': msg})


def page(request, id):

    request.session['rid'] = id
    uid = request.session.get('user_id')
    rest = list(Restaurant.objects.raw("SELECT * FROM restaurant WHERE Rid = %s", [id]))[0]
    fvr = list(Favorite.objects.raw("SELECT * FROM favorite WHERE user_id = %s and restaurant_id = %s", [uid, id]))
    menu  = Item.objects.raw("SELECT * FROM item WHERE store_id = %s and avaliable = True", [id])
    menus = []
    for i in menu:
        menus.append({"name": i.name,"price": i.price, "desc": i.desc,"pic": i.picture})
    tag = Tag.objects.raw("SELECT t.id, t.name FROM tag t JOIN restaurant_tag r ON r.tag_id = t.id WHERE r.restaurant_id = %s;", [id])
    tags = []
    for t in tag:
        tags.append(t.name)
    restaurant_info = {
    "id": id,
    "name": rest.name,
    "tags": tags,
    "desc": rest.desc,
    "menu": menus,
    "address": rest.address,
    "img": rest.picture,
    }
    return render(request, "pages.html", {"restaurant": restaurant_info, "fvr": fvr})


def your_django_cart_view(request):
    if request.method == 'POST':
        try:
            cart_data = json.loads(request.body)
            # At this point, you have the cart_data (which corresponds to your cartItems array)
            # You can now perform actions that don't necessarily involve the database immediately.

            # Example: Logging the received cart data
            print("Received cart data:", cart_data)

            # Example: Storing in session
            request.session['cart'] = cart_data

            # Example: Sending a response without database interaction
            return JsonResponse({'status': 'success', 'message': 'Cart data received'})

        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'Invalid JSON data'}, status=400)
    else:
        return JsonResponse({'status': 'error', 'message': 'Only POST requests are allowed'}, status=405)
def view_cart(request):
    cart_data_from_session = request.session.get('cart', [])
    context = {'cart_items': cart_data_from_session}
    return render(request, "cart.html", context)

def contShop(request):
    rid = request.session.get('rid')
    return redirect('pages', id=rid)

def vieworder(request):
    cart_data = request.session.get('cart', [])
    price = 0
    for i in cart_data:
        price += int(i['price'])
    return render(request, 'vieworder.html', {'price': price})

def checkout(request):
    last = Order.objects.raw('SELECT * FROM "order" ORDER BY id DESC LIMIT 1;')
    lastid = int(last[0].id)
    oid = lastid + 1
    rid = int(request.session.get('rid'))
    uid = int(request.session.get('user_id'))
    cart_data = request.session.get('cart', [])
    dtime = 0
    price = 0
    amount = 0
    for i in cart_data:
        p = int(i['price'])
        q = int(i['quantity'])
        amount += q
        price += p * q
    placetime = datetime.now()
    dest = str(request.POST.get('dest'))
    status = 'on route'
    location = '22.6300545:120.2639648'
    with connection.cursor() as cursor:
        cursor.execute('INSERT INTO "order" (id, items, price, created_at, user_id, restaurant_id, destination, status, time, location) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (oid, amount, price, placetime, uid, rid, dest, status, dtime, location))

    return redirect('/orderplaced/')

def orderplaced(request):
    return render(request, 'orderplaced.html')

def addFvr(request):
    last = Favorite.objects.raw('SELECT * FROM "favorite" ORDER BY id DESC LIMIT 1;')
    if last:
        lastid = int(last[0].id)
        fid = lastid + 1
    else:
        fid = 1
    rid = request.session.get('rid')
    uid = request.session.get('user_id')
    with connection.cursor() as cursor:
        cursor.execute('INSERT INTO "favorite" (id, restaurant_id, user_id) VALUES(%s, %s, %s)', (fid, rid, uid))

    return redirect('pages', id = rid)

def remFvr(request):
    rid = request.session.get('rid')
    uid = request.session.get('user_id')
    with connection.cursor() as cursor:
        cursor.execute('DELETE FROM "favorite" WHERE restaurant_id = %s and user_id = %s', [rid, uid])

    return redirect('pages', id=rid)

def fav(request, userid):
    rows = Favorite.objects.raw('SELECT * FROM favorite WHERE user_id = %s', [userid])

    fav_re = []
    for row in rows:
        # tags = Tag.objects.raw("SELECT t.name FROM tag t JOIN restaurant_tag r ON t.id = r.tag_id WHERE r.restaurant_id = %s;", [row.Rid])
        # tag = []
        # for t in tags:
        #     tag.append(t.name)
        # menus = []
        # Items = Item.objects.raw("SELECT * FROM item WHERE restaurant_id = %s", [row.Rid])
        # for m in Items:
        #     menus.append({"name": m.name, "price": m.price, "pic": static(m.picture), "desc": m.desc})
        tempRes = Restaurant.objects.raw('SELECT * FROM "restaurant" WHERE Rid = %s', [row.restaurant_id])
        fav_re.append({
            "id": tempRes[0].Rid,
            "name": tempRes[0].name,
            # "tags": tag,
            # "description": row.desc,
            # "menu": menus,
            # "address": row.address,
            "img": static(tempRes[0].picture),
        })

    return render(request, "favorite.html",{'favs':fav_re})



def orderUser(request, userid):
    orders = Order.objects.raw("SELECT * FROM 'order' WHERE user_id = %s AND status='Complete'", [userid])
    
    UserOrders = []
    for o in orders:
      
        
        rest = Restaurant.objects.get(Rid=o.restaurant_id)
        
        ord = {
            "id": o.id,
            
            "price": o.price,
            "created": o.created_at,
            "time": o.time,
            "destination": o.destination,
            "deliveryP": o.delivery_person_id,
            "restaurant": rest.name,   
            "status": o.status, 
        }
        UserOrders.append(ord)
    return render(request, "orders.html", {'order':UserOrders, 'user': userid})

@csrf_exempt
def login_view(request):

    if request.method == "POST":
        form_type = request.POST.get("form_type")

        if form_type == 'login':
            form = UserLoginForm(request.POST)
            if form.is_valid():
                email = form.cleaned_data['email']
                password = form.cleaned_data['password']
                user = User.objects.get(email = email)
                if user is not None:
                    user_id = user.user_id
                    if Customer.objects.filter(user_ptr_id= user_id).exists():
                        request.session['role'] = 'customer'
                    elif Vendor.objects.filter(user_ptr_id= user_id).exists():
                        request.session['role'] = 'vendor'
                    elif DeliveryP.objects.filter(user_ptr_id= user_id).exists():
                        request.session['role'] = 'delivery'
                    request.session['user_id'] = user.pk
                    print(user.pk)
                    return redirect('index')


        elif form_type == 'register':
            form = UserRegistrationForm(request.POST)
            if form.is_valid():

                user = User(name=form.cleaned_data['username'], email=form.cleaned_data['email'] ,password=form.cleaned_data['password'])
                user.save()

                user_type = form.cleaned_data['role']
                if user_type == 'customer':
                    customer = Customer(user_ptr_id = user.pk)
                    customer.save_base(raw = True) #避免重複保存User
                elif user_type == 'deliverer':
                    deliverer = DeliveryP(user_ptr_id = user.pk)
                    deliverer.last_delivery_time = timezone.now()
                    deliverer.save_base(raw = True)
                elif user_type == 'vendor':
                    vendor = Vendor(user_ptr_id = user.pk)
                    vendor.save_base(raw = True)
                return redirect('login')

    return render(request, "login.html")


def ShowOrderDetails(request, OrderID, DeliID):
    order = list(Order.objects.raw("SELECT * FROM 'order' WHERE id = %s", [OrderID]))[0]
    orderItemsId = order.items.split(",")
    foods = []
    for id in orderItemsId:
        food = list(Item.objects.raw("SELECT * FROM item WHERE id = %s", [id]))[0]

        foods.append({"name":food.name, "price": food.price})
    restaurant = Restaurant.objects.get(Rid=order.restaurant_id)
    restaurant_name = restaurant.name
    restaurant_address = restaurant.address
    customer = Customer.objects.get(user_id = order.user_id)
    details = {
        "id": order.id,
        "items": json.dumps(foods),
        "price": order.price,
        "created": order.created_at,
        "restaurant": restaurant_name,
        "customer": customer.name,
        "destination": order.destination,
        "rest_dest": restaurant_address,
        "cust_id": order.user_id
    }
    return render(request, "Details.html", {'detail': [details], "deliP": DeliID, "CanTake": True, 'CanComplete': False})

@csrf_exempt
def TakeOrder(request,orderid, deliID):
    if request.method == 'POST':
     
        try:
            order = Order.objects.get(id=orderid)
            delivery_person = User.objects.get(user_id=deliID)
            order.delivery_person_id = delivery_person
            order.status = 'pending'
            order.save()
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
            "orders",
            {
            "type": "order_update",
            "message": f"Order {orderid} taken",
            }
            )
            return JsonResponse({'success': True})
        except order.DoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)
            
    return JsonResponse({'error': 'Invalid method'}, status=405)

def vendor_orders_api(request,Rid):
    orders = Order.objects.raw("SELECT * FROM 'order' WHERE status = 'pending' AND restaurant_id = %s", [Rid])
    data = []
    for o in orders:
            itemId = o.items.split(",")
            itms = []
            for i in itemId:
                item = list(Item.objects.raw("SELECT * FROM item WHERE id = %s", [i]))[0]
                itms.append({
                    "name": item.name,
                    "price":item.price,
                    "desc": item.desc,
                }) 
            data.append({
                "id": o.id,
                "items": itms,
                'price': o.price,
                "created": o.created_at,
                "customer": o.user_id,
                "delivery": o.delivery_person_id,
            })

    return JsonResponse(data)


def ShowCurrentOrder(request, deliID):
    Current = Order.objects.raw("SELECT * FROM 'order' WHERE delivery_person_id = %s AND status = 'pending' OR status='on route' OR status='Food Done'", [deliID]) 
    CurrentOrders = []
    for c in Current:
        foods = []
        orderItemsId = c.items.split(",")
        for id in orderItemsId:
            food = list(Item.objects.raw("SELECT * FROM item WHERE id = %s", [id]))[0]

            foods.append({"name":food.name, "price": food.price})
        restaurant = Restaurant.objects.get(Rid=c.restaurant_id)
        restaurant_name = restaurant.name
        restaurant_address = restaurant.address
        customer = Customer.objects.get(user_id = c.user_id)
        if c.status == "on route":
            canStartNav = False
        else:
            canStartNav = True
        details = {
        "id": c.id,
        "items": json.dumps(foods),
        "price": c.price,
        "created": c.created_at,
        "restaurant": restaurant_name,
        "customer": customer.name,
        "destination": c.destination,
        "rest_dest": restaurant_address,
        "cust_id": c.user_id,
        "status": c.status,
        "canStartNav": canStartNav
        }
        CurrentOrders.append(details)

    return render(request, "Details.html", {'detail': CurrentOrders, "deliP": deliID, "CanTake":False, "CanComplete":True})


def ShowVendorOrder(request, Oid, VendorID):
    order = list(Order.objects.raw("SELECT * FROM 'order' WHERE id=%s",[Oid]))[0]
    orderItemsId = order.items.split(",")
    foods = []
    for id in orderItemsId:
        food = list(Item.objects.raw("SELECT * FROM item WHERE id = %s", [id]))[0]

        foods.append({"name":food.name, "price": food.price})
    customer = Customer.objects.get(user_id = order.user_id)
    
    details = {
        "id": order.id,
        "items": foods,
        "price": order.price,
        "created": order.created_at,
        "customer": customer.name,
        "delivery": order.delivery_person_id
        
    }
    return render(request, "VendorOrder.html", {"details": [details], "complete": True, "vendor": VendorID})

@csrf_exempt
def PrepOrder(request, Oid):
    if request.method == 'POST':
     
        try:
            order = Order.objects.get(id=Oid)
            order.status = 'Food Done'
            order.save()
            return JsonResponse({'success': True})
        except order.DoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)
            
    return JsonResponse({'error': 'Invalid method'}, status=405)

@csrf_exempt
def CompOrder(request, Orderid, Userid):
    if request.method == 'POST':
     
        try:
            order = Order.objects.get(id=Orderid)
            delivery = order.delivery_person
            order.status = "Complete"
            order.save()
            
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
            f"user_{Userid}",
        {
            'type': 'send_order_complete',
            'message': f"Your order #{Orderid} has been marked as completed by delivery {delivery}"
        }
            )
            Inbox.objects.create(message = f"Your order #{Orderid} has been marked as completed by delivery {delivery}", user_id = Userid)

            return JsonResponse({'success': True})
        except order.DoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)
            
    return JsonResponse({'error': 'Invalid method'}, status=405)


def updateInbox(request, userid):
    msgs = Inbox.objects.raw("SELECT * FROM inbox WHERE user_id = %s", [userid])
    data = []
    for m in msgs:
            data.append({
            "message": m.message,
            "timestamp": m.timestamp
        })

    return JsonResponse(data)



def ViewInbox(request, userid):
    msgs = Inbox.objects.raw("SELECT * FROM inbox WHERE user_id = %s", [userid])
    data = []
    for m in msgs:
            data.append({
            "message": m.message,
            "timestamp": m.timestamp
        })
            
    return render(request, "inbox.html", {"msg": data})


def StartNav(request, Oid):
    o = Order.objects.get(id=Oid)
    o.status = "on route"
    o.save()
    Rest = Restaurant.objects.get(Rid = o.restaurant_id)
    coords = get_coordinates(Rest.address)
    if(coords):
        Rest.latitude = coords[0]
        Rest.longitude = coords[1]
        Rest.save()
    
    return render(request, "Navigation.html", {"orderID": Oid, "RestAddress":coords})


def get_coordinates(address):
    newAddr = force_trim_to_road_name(address)
    print(f"[DEBUG] Attempting to geocode address: {newAddr}")
    geolocator = Nominatim(user_agent="DjangoUberApp") 
    try:
        location = geolocator.geocode(newAddr)
        if location:
            print(f"[DEBUG] Geocoding success: {location.raw}")
            return (location.latitude, location.longitude)
        else:
            print("[ERROR] Address not found")
            return None
    except GeocoderTimedOut:
        print("[ERROR] Geocoding timed out")
        return None
    except GeocoderServiceError as e:
        print(f"[ERROR] Geocoder service error: {e}")
        return None
    


def force_trim_to_road_name(address): #force address to match specifications

    # Remove leading postal code if any (3 to 5 digits)
    address = re.sub(r'^\d{3,5}', '', address)

    # Match pattern: 市 + 區 + 路(可含一/二段)
    match = re.match(r'.*?市.*?區.*?路[一二三四五六七八九十]?(段)?', address)
    if match:
        return match.group(0)

    # If not match, return as-is (may be already trimmed or malformed)
    return address

@csrf_exempt
def AddRestaurant(request, user):
    print("Path:", request.path)
    print("User param:", user)
    if request.method == "POST":
        name = request.POST.get("RestName")
        desc = request.POST.get("RestDesc")
        address = request.POST.get("RestAddress")
        pic_file = request.FILES.get("RestPic")
        #if pic_file:
         #   filename = pic_file.name
         #   filepath = os.path.join("static/assets", filename)
          #  with open(filepath, 'wb+') as destination:
           #     for chunk in pic_file.chunks():
           #         destination.write(chunk)
           #         pic_path = f"assets/{filename}"
        #else:
           # pic_path = ""
        opening = request.POST.get("OpeningTime")
        closing = request.POST.get("ClosingTime")
        tag_ids = request.POST.getlist("ResTags")
        opening_time = datetime.datetime.strptime(opening, "%H:%M").time()
        closing_time = datetime.datetime.strptime(closing, "%H:%M").time()
        if Restaurant.objects.filter(name=name, address=address).exists():
            return JsonResponse({
                "status": "error",
                "message": "A restaurant with the same name and address already exists."
            }, status=400)
        restaurant = Restaurant.objects.create(
            name=name,
            desc=desc,
            address=address,
            picture=pic_file, #replace this if saving to static
            opening_time=opening_time,
            closing_time=closing_time
        )
        print(user)
        vendor = Vendor.objects.get(user_id = user)
        vendor.store = restaurant
        vendor.save()
        for t in tag_ids:
            tag = Tag.objects.get(id = t)
            RestaurantTag.objects.create(
                restaurant = restaurant,
                tag = tag,
            )
        return JsonResponse({
            "status": "success",
            "restaurant_id": restaurant.Rid
        })

    return JsonResponse({"error": "Invalid request method"}, status=405)


@csrf_exempt
def AddMenuItems(request, Rid):
    if request.method == "POST":
        name = request.POST.get("ItemName")
        desc = request.POST.get("ItemDesc")
        price = request.POST.get("ItemPrice")
        pic = request.FILES.get("ItemPic")
        rest = Restaurant.objects.get(Rid=Rid)
        if Item.objects.filter(name=name, store=Rid).exists():
            return JsonResponse({
                "status": "error",
                "message": "A Item with the same name and RId already exists."
            }, status=400)
        it = Item.objects.create(
            name = name,
            price = price,
            desc = desc,
            picture = pic,
            store = rest,
        )
        return JsonResponse({
            "status": "success",
            "restaurant_id": it.id
        })
    return JsonResponse({"error": "Invalid request method"}, status=405)


def ViewMenu(request, user):
    vendor = Vendor.objects.get(user_id = user)
    Rid = vendor.store_id
    items = Item.objects.raw("SELECT * FROM item WHERE store_id = %s", [Rid])
    itms = []
    for i in items:

        itms.append({
            "id": i.id,
            "name": i.name,
            "price":i.price,
            "desc": i.desc,
            "picture": i.picture,
            "avaliable": i.avaliable
        })

    return render(request, "Menu.html", {"items": itms, "Rid": Rid})



@csrf_exempt
def UpdateStatus(request, ItemId):
    if request.method == "POST":
        It = Item.objects.get(id = ItemId)
        if It.avaliable:
            It.avaliable = False
            It.save()
        else:
            It.avaliable = True
            It.save()
        return JsonResponse({
            "status": "success",
            "avaliable": It.avaliable
        })
    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def deleteItem(request, ItemId):
    if request.method == "POST":
        try:
            item = Item.objects.get(id=ItemId)
            item.delete()
            return JsonResponse({"status": "success"})
        except Item.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Item not found"}, status=404)
    return JsonResponse({"error": "Invalid request method"}, status=405)


def ShowUserCurrent(request,user):
    CurrentOrder = Order.objects.raw("SELECT * FROM 'order' WHERE user_id = %s AND status != 'Complete'", [user])
    ors = []
    for c in CurrentOrder:
        foods = []
        orderItemsId = c.items.split(",")
        for id in orderItemsId:
            food = list(Item.objects.raw("SELECT * FROM item WHERE id = %s", [id]))[0]

            foods.append({"name":food.name, "price": food.price})
        restaurant = Restaurant.objects.get(Rid=c.restaurant_id)
        restaurant_name = restaurant.name



        details = {
        "id": c.id,
        "items": json.dumps(foods),
        "price": c.price,
        "created": c.created_at,
        "restaurant": restaurant_name,
        "delivery": c.delivery_person_id,
        "destination": c.destination,

        "status": c.status,
        }
        ors.append(details)
    return render(request, "UserOrderDetails.html",{"details": ors, "user": user})



def ShowTracker(request, order):
    return render(request, "Tracker.html", {"orderid": order})

@csrf_exempt
def UpdateItem(request, Mid):
    if request.method == "POST":
        name = request.POST.get("ItemName")
        desc = request.POST.get("ItemDesc")
        price = request.POST.get("ItemPrice")
        pic = request.FILES.get("ItemPic")
        It = Item.objects.get(id=Mid)
        It.name = name
        It.price = price
        It.desc = desc
        if(pic):
            It.picture = pic
        It.save()
        
        
        
        return JsonResponse({
            "status": "success",
            "id": It.id
        })
    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def search(request):
    if request.method == "POST":
            name = request.POST.get("search")
            item = Item.objects.filter(name__icontains=name).first()
            
            return JsonResponse({
                "status": "success",
                "id": item.id,
                "name": item.name,
                "price": item.price,
                
                "desc": item.desc
            })
    return JsonResponse({"error": "Invalid request method"}, status=405)