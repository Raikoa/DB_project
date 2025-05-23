import datetime
import os
import re
from django.shortcuts import render, redirect
import uuid
from django.db import connection
from datetime import datetime
from django.shortcuts import render, redirect
from django.core.files.base import ContentFile
from django.shortcuts import render
from django.templatetags.static import static
import numpy as np
import pandas as pd
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
import osmnx as ox
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
    user_id = request.session.get('user_id')
    test_user = User.objects.get(user_id = user_id)
    #test_user= Vendor.objects.first()
    #user = request.user

    # if isinstance(test_user, Customer):
    #     role = 'customer'
    # elif isinstance(test_user, Vendor):
    #     role = 'vendor'
    # elif isinstance(test_user, DeliveryP):
    #     role = 'delivery'

    role = request.session.get('role')
    print(role)
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
       tags = Tag.objects.raw("SELECT * FROM tag")
       tgs = []
       for t in tags:
           tgs.append({
               "id": t.id,
               "name": t.name
           })
       data = []
       for r in restaurants:
           data.append({
               "id": r.Rid,
                "name": r.name,
                "address": r.address,
                "img": r.picture,
           })
       return render(request, "index.html", {'Test':data, 'Role': role, 'Username': test_user.name, 'userid': test_user.user_id, 'msg': msg, 'tags': tgs})


def page(request, id):

    request.session['rid'] = id
    rest = list(Restaurant.objects.raw("SELECT * FROM restaurant WHERE Rid = %s", [id]))[0]
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
    return render(request, "pages.html", {"restaurant": restaurant_info})


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

def checkout(request):
    last = Order.objects.raw('SELECT * FROM "order" ORDER BY id DESC LIMIT 1;')
    lastid = int(last[0].id)
    oid = lastid + 1
    rid = int(request.session.get('rid'))
    uid = int(request.session.get('uid'))
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
    dest = 'address'
    status = 'on route'
    location = '22.6300545:120.2639648'
    with connection.cursor() as cursor:
        cursor.execute('INSERT INTO "order" (id, items, price, created_at, user_id, restaurant_id, destination, status, time, location) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', (oid, amount, price, placetime, uid, rid, dest, status, dtime, location))

    return redirect('/orderplaced/')

def orderplaced(request):
    return render(request, 'orderplaced.html')

def fav(request, userid):
    rows = Restaurant.objects.raw("SELECT r.* FROM favorite f JOIN restaurant r ON f.restaurant_id = r.Rid WHERE f.user_id = %s;", [userid])

    fav_re = []
    for row in rows:
        tags = Tag.objects.raw("SELECT t.name FROM tag t JOIN restaurant_tag r ON t.id = r.tag_id WHERE r.restaurant_id = %s;", [row.Rid])
        tag = []
        for t in tags:
            tag.append(t.name)
        menus = []
        Items = Item.objects.raw("SELECT * FROM item WHERE restaurant_id = %s", [row.Rid])
        for m in Items:
            menus.append({"name": m.name, "price": m.price, "pic": static(m.picture), "desc": m.desc})
        fav_re.append({
            "id": row.Rid,
                "name": row.name,
                "tags": tag,
                "description": row.desc,
                "menu": menus,
                "address": row.address,
                "img": static(row.picture),
        })

    return render(request, "favorite.html",{'favs':fav_re})



def orderUser(request, userid):
    orders = Order.objects.raw("""
        SELECT 
            o.id,
            o.price,
            o.created_at,
            o.destination,
            o.status,
            o.items,
            o.user_id,
            o.delivery_person_id,
            o.restaurant_id,
            u.name AS delivery_person_name,
            r.name AS restaurant_name
        FROM "order" o
        LEFT JOIN "user" u ON o.delivery_person_id = u.user_id
        INNER JOIN restaurant r ON o.restaurant_id = r.Rid
        WHERE o.user_id = %s AND o.status = 'Complete'
    """, [userid])
    
    UserOrders = []
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
        ord = {
            "id": o.id,
            "price": o.price,
            "created": o.created_at,
            "destination": o.destination,
            "delivery_person_name": o.delivery_person_name or "Not Assigned",
            "restaurant": o.restaurant_name,
            "status": o.status,
            "items": json.dumps(itms)
        }
        UserOrders.append(ord)

    return render(request, "orders.html", {'order': UserOrders, 'user': userid})

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
            order.taken = timezone.now()
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
            add_points_to_deli(order.id, order.points)
            try:
                delivery_person = DeliveryP.objects.get(user_id=delivery.user_id)
                delivery_person.last_delivery_time = timezone.now()
                delivery_person.save()
            except DeliveryP.DoesNotExist:
                print("Error: User is not a delivery person.")
           
            
            order.status = "Complete"
            order.completed = timezone.now()
            order.save()
            
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
            f"user_{Userid}",
        {
            'type': 'send_order_complete',
            'message': f"Your order #{Orderid} has been marked as completed by delivery ({delivery.id})"
        }
            )
            Inbox.objects.create(message = f"Your order #{Orderid}# has been marked as completed by delivery ({delivery.id})", user_id = Userid)

            return JsonResponse({'success': True})
        except order.DoesNotExist:
            return JsonResponse({'error': 'Order not found'}, status=404)
            
    return JsonResponse({'error': 'Invalid method'}, status=405)


def updateInbox(request, userid):
    msgs = Inbox.objects.raw("SELECT * FROM inbox WHERE user_id = %s", [userid])
    data = []
    for m in msgs:
            match = re.search(r"#(\d+)#", m.message)
            reviewed = False
            if match:
                order_id = int(match.group(1))
                try:
                    order = Order.objects.get(id=order_id)
                    reviewed = order.Review != "-"  # Or however you store default/no review
                except Order.DoesNotExist:
                    pass
            data.append({
            "message": m.message,
            "timestamp": m.timestamp,
            "reviewed": reviewed
        })

    return JsonResponse(data, safe=False)



def ViewInbox(request, userid):
    msgs = Inbox.objects.raw("SELECT * FROM inbox WHERE user_id = %s", [userid])
    
    data = []
    for m in msgs:
            data.append({
            "message": m.message,
            "timestamp": m.timestamp
        })
            
    return render(request, "inbox.html", {"msg": data, "userid": userid})


def StartNav(request, Oid):
    o = Order.objects.get(id=Oid)
    o.status = "on route"
    o.save()
    destination = o.destination
    Rest = Restaurant.objects.get(Rid = o.restaurant_id)
    coords = get_coordinates(Rest.address)
    if(coords):
        Rest.latitude = coords[0]
        Rest.longitude = coords[1]
        Rest.save()
    Order_end_coords = get_coordinates(destination)
    if(Order_end_coords):
        o.destination_lat = Order_end_coords[0]
        o.destination_lng = Order_end_coords[1]
        o.save()
    return render(request, "Navigation.html", {"orderID": Oid, "RestAddress":coords, "Order_end_coords": Order_end_coords, "preview": False})


#def get_coordinates(address):
    #newAddr = force_trim_to_road_name(address)
    #print(f"[DEBUG] Attempting to geocode address: {newAddr}")
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
    
def get_coordinates(address):
    try:
        # Properly encode the address for URL use
        #encoded_address = urllib.parse.quote(address)

        # Your API key from Django settings
        api_key = "AIzaSyBElfTjB_ODR7adcc1xYSO1f0itjz77Lr4"

        # Construct the API URL
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={address}&key={api_key}"

        # Make the request
        response = requests.get(url)
        data = response.json()

        # Check for valid response
        if data['status'] == 'OK':
            location = data['results'][0]['geometry']['location']
            print(f"[DEBUG] Geocoding success: {location}")
            return location['lat'], location['lng']
        else:
            print(f"[ERROR] Geocoding failed: {data['status']}")
            return None

    except Exception as e:
        print(f"[ERROR] Google Maps API request failed: {e}")
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



def heatmap(request, Oid):
    order = Order.objects.get(id = Oid)
    destination = order.destination
    rest_id = order.restaurant_id
    rest = Restaurant.objects.get(Rid = rest_id)
    rest_dest = rest.address
    location = get_coordinates(rest_dest)
    if(location):
        rest.latitude = location[0]
        rest.longitude = location[1]
        rest.save()
    Order_end_coords = get_coordinates(destination)
    if(Order_end_coords):
        order.destination_lat = Order_end_coords[0]
        order.destination_lng = Order_end_coords[1]
        order.save()
    return render(request,"Navigation.html", {"orderID": Oid, "RestAddress":location, "Order_end_coords": Order_end_coords, "preview": True})



@csrf_exempt
def getCoords(request, Oid):
    if request.method == "POST":
        order = Order.objects.get(id = Oid)
        laln = order.location.split(":")
        lat = laln[0]
        lng = laln[1]
        return JsonResponse({
                "status": "success",
                "lat": lat,
                "lng": lng
            })
    return JsonResponse({"error": "Invalid request method"}, status=405)



def startEstimate(request):
        return render(request, "estimateSelect.html")


def AreaEstimate(request,area):
        translate_city_to_english(area)
        return render(request, "estimateArea.html", {"area":area, "Deli": False})

def translate_city_to_english(chinese_city):
    match chinese_city:
        case "台北市": return "Taipei"
        case "新北市": return "New Taipei"
        case "桃園市": return "Taoyuan"
        case "台中市": return "Taichung"
        case "台南市": return "Tainan"
        case "高雄市": return "Kaohsiung"
        case "基隆市": return "Keelung"
        case "新竹市": return "Hsinchu"
        case "嘉義市": return "Chiayi"
        case "新竹縣": return "Hsinchu"
        case "苗栗縣": return "Miaoli"
        case "彰化縣": return "Changhua"
        case "南投縣": return "Nantou"
        case "雲林縣": return "Yunlin"
        case "嘉義縣": return "Chiayi"
        case "屏東縣": return "Pingtung"
        case "宜蘭縣": return "Yilan"
        case "花蓮縣": return "Hualien"
        case "台東縣" | "臺東縣": return "Taitung"
        case "澎湖縣": return "Penghu"
        case "金門縣": return "Kinmen"
        case "連江縣": return "Lienchiang"
        case _: return chinese_city

# def get_bounds(city_name):
#     try:
#         gdf = ox.geocode_to_gdf(city_name)
#         bounds = gdf.bounds.iloc[0]
#         return {
#             "min_lat": bounds["miny"],
#             "max_lat": bounds["maxy"],
#             "min_lng": bounds["minx"],
#             "max_lng": bounds["maxx"]
#         }
#     except Exception as e:
#         print(f"[City Bounds Error] {str(e)}")
#         return None
    

# def generate_grid(city_name, step=0.01):
#     city_bounds = get_bounds(city_name)
#     if not city_bounds:
#         return pd.DataFrame()

#     lat_range = np.arange(city_bounds["min_lat"], city_bounds["max_lat"], step)
#     lng_range = np.arange(city_bounds["min_lng"], city_bounds["max_lng"], step)

#     grid_points = [
#         {"lat": lat, "lng": lng}
#         for lat in lat_range
#         for lng in lng_range
#     ]
#     return pd.DataFrame(grid_points)


@csrf_exempt
def getCity(request, Oid):
    if request.method == "POST":
        order = Order.objects.get(id=Oid)
        raw_address = order.destination
        print(raw_address)
        city = extract_city(raw_address)
        eng_city = translate_city_name(city)
        dest_lat, dest_lng = order.destination_lat, order.destination_lng
        if(dest_lat is None or dest_lng is None):
            dest_lat, dest_lng = get_coordinates(raw_address)
            print(get_coordinates(raw_address))
        return JsonResponse({
            "status": "success",
            "city": eng_city,
            "lat": dest_lat,
            "lng": dest_lng
        })
    return JsonResponse({"error": "Invalid request method"}, status=405)



def extract_city(address):
    match = re.search(r"(台北市|新北市|台中市|台南市|高雄市|基隆市|新竹市|嘉義市|桃園市|宜蘭縣|新竹縣|苗栗縣|彰化縣|南投縣|雲林縣|嘉義縣|屏東縣|臺東縣|花蓮縣|澎湖縣|金門縣|連江縣)", address)
    if match:
        return match.group(0)
    return "未知地區"




def AreaEstimateDeli(request,area, Oid):
        order = Order.objects.get(id=Oid)
        raw_address = order.destination
        dest_lat, dest_lng = order.destination_lat, order.destination_lng
        Rest = order.restaurant
      
        rest_lat = Rest.latitude
        rest_lng = Rest.longitude
        if(rest_lat is None or rest_lng is None):
            rest_addr = Rest.address
            rest_lat, rest_lng = get_coordinates(rest_addr)

        if(dest_lat is None or dest_lng is None):
            dest_lat, dest_lng = get_coordinates(raw_address)
        return render(request, "estimateArea.html", {"area":area, "dest_lat": dest_lat, "dest_lng": dest_lng, "Deli": True, 'rest_lat': rest_lat, 'rest_lng': rest_lng, 'Oid': Oid})


def translate_city_name(ch_name):
    match ch_name:
        case "臺北市" | "台北市":
            return "Taipei"
        case "新北市":
            return "New Taipei"
        case "桃園市":
            return "Taoyuan"
        case "臺中市" | "台中市":
            return "Taichung"
        case "臺南市" | "台南市":
            return "Tainan"
        case "高雄市":
            return "Kaohsiung"
        case "基隆市":
            return "Keelung"
        case "新竹市":
            return "Hsinchu"
        case "嘉義市":
            return "Chiayi"
        case "新竹縣":
            return "Hsinchu County"
        case "苗栗縣":
            return "Miaoli"
        case "彰化縣":
            return "Changhua"
        case "南投縣":
            return "Nantou"
        case "雲林縣":
            return "Yunlin"
        case "嘉義縣":
            return "Chiayi County"
        case "屏東縣":
            return "Pingtung"
        case "宜蘭縣":
            return "Yilan"
        case "花蓮縣":
            return "Hualien"
        case "臺東縣" | "台東縣":
            return "Taitung"
        case "澎湖縣":
            return "Penghu"
        case "金門縣":
            return "Kinmen"
        case "連江縣":
            return "Lienchiang"
        case _:
            return ch_name  # fallback, just in case


def RateOrder(request, Oid, Uid):
    return render(request, "Rate.html",{"Oid": Oid, "Uid": Uid})

@csrf_exempt
def ProcessOrder(request, Oid, score, comment):
    if request.method == "POST":
        order = Order.objects.get(id=Oid)
        point = 0
        if(score <= 2):
            point = 0
        
        if(score > 2 and score < 4):
            point = 1
        if(score >= 4):
            point = 2
        order.points = order.points + point
        order.Review = str(score) + ":" + comment
        add_points_to_deli(order.id, score)
        order.save()
        
        return JsonResponse({
            "status": "success"
            
        })
    return JsonResponse({"error": "Invalid request method"}, status=405)



def add_points_to_deli(Oid, points):
    order = Order.objects.get(id=Oid)
    user = order.delivery_person
    try:
        delivery_person = DeliveryP.objects.get(user_id=user.user_id)
        delivery_person.Score += points
        delivery_person.save()
    except DeliveryP.DoesNotExist:
        print("Error: User is not a delivery person.")



def Rankings(request):
    data = DeliveryP.objects.raw("SELECT * FROM delivery_person ORDER BY score DESC")
    delis = []
    for d in data:
        delis.append({
            "id": d.user_id,
            "name": d.name,
            "score": d.Score
        })
    return render(request, "Rankings.html", {"delis": delis})

@csrf_exempt
def checkReviewed(request, Oid):
    if request.method == "POST":
        valid = True
        order = Order.objects.get(id = Oid)
        if order.Review != "-":
            valid = False
        
        return JsonResponse({
            "Valid": valid
            
        })
    return JsonResponse({"error": "Invalid request method"}, status=405)



@csrf_exempt
def SearchRest(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            name = data.get("name", "").strip()
            tags = data.get("tags", [])

            sql = """
                SELECT DISTINCT r.Rid, r.name, r.desc, r.status, r.picture, r.address
                FROM restaurant r
                LEFT JOIN restaurant_tag rt ON r.Rid = rt.restaurant_id
                LEFT JOIN tag t ON rt.tag_id = t.id
                WHERE 1=1
            """
            params = []

            if name:
                sql += " AND r.name LIKE %s"
                params.append(f"%{name}%")

            if tags:
                tag_count = len(tags)
                sql += f"""
                    AND r.Rid IN (
                        SELECT restaurant_id
                        FROM restaurant_tag
                        WHERE tag_id IN ({','.join(['%s'] * tag_count)})
                        GROUP BY restaurant_id
                        HAVING COUNT(DISTINCT tag_id) = %s
                    )
                """
                params.extend(tags)
                params.append(tag_count)

            with connection.cursor() as cursor:
                cursor.execute(sql, params)
                rows = cursor.fetchall()

            results = []
            restaurant_ids = []

            for row in rows:
                rest_id, rest_name, desc, status, picture, address = row
                restaurant_ids.append(rest_id)
                results.append({
                    "id": rest_id,
                    "name": rest_name,
                    "desc": desc,
                    "status": status,
                    "picture": f"/media/{picture}" if picture else "",
                    "address": address,
                    "tags": []  # will be filled in next step
                })

            # Get all tags for the listed restaurants
            if restaurant_ids:
                with connection.cursor() as cursor:
                    format_ids = ','.join(['%s'] * len(restaurant_ids))
                    tag_sql = f"""
                        SELECT rt.restaurant_id, t.name
                        FROM restaurant_tag rt
                        JOIN tag t ON rt.tag_id = t.id
                        WHERE rt.restaurant_id IN ({format_ids})
                    """
                    cursor.execute(tag_sql, restaurant_ids)
                    tag_rows = cursor.fetchall()

                # Organize tags by restaurant_id
                tags_map = {}
                for rest_id, tag_name in tag_rows:
                    tags_map.setdefault(rest_id, []).append(tag_name)

                # Attach tags to results
                for rest in results:
                    rest["tags"] = tags_map.get(rest["id"], [])

            return JsonResponse({"restaurants": results}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)
    return JsonResponse({"error": "Invalid request method"}, status=405)

@csrf_exempt
def GetInbox(request, userid):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            msgs = data.get("query", "").strip()

            
            query = """
                SELECT * FROM inbox
                WHERE user_id = %s AND message LIKE %s
                ORDER BY timestamp DESC
            """
            inbox = Inbox.objects.raw(query, [userid, f"%{msgs}%"])

            result = []
            for msg in inbox:
                result.append({
                    "id": msg.id,
                    "message": msg.message,
                    "is_read": msg.is_read,
                    "timestamp": msg.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                })

            return JsonResponse({"messages": result}, status=200)
        except json.JSONDecodeError:
            return JsonResponse({"error": "Invalid JSON"}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=405)