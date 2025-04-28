from django.shortcuts import render
from django.templatetags.static import static
from database.models import Customer, Vendor, DeliveryP, Favorite,RestaurantTag, Tag, Item, Restaurant, Order, User # type: ignore
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from channels.layers import get_channel_layer # type: ignore
from asgiref.sync import async_to_sync
import json
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
    test_user= Vendor.objects.first()
    #user = request.user

    role = None
    if isinstance(test_user, Customer):
        role = 'customer'
    elif isinstance(test_user, Vendor):
        role = 'vendor'
    elif isinstance(test_user, DeliveryP):
        role = 'delivery'

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
        return render(request, "index.html", {'Role': role, 'Username': test_user.name, 'userid': test_user.user_id, 'Orders':order_queue})
    
    if role == 'vendor':
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
        return render(request, "index.html", {'Role': role, 'Username': test_user.name, 'userid': test_user.user_id, 'Orders':order_inc})

    return render(request, "index.html", {'Test':data, 'Role': role, 'Username': test_user.name, 'userid': test_user.user_id})


def page(request, id):
    data = give_exp_func()
    restaurant = next((r for r in data if r["id"] == id), None)
    rest = Restaurant.objects.raw("SELECT * FROM restaurant WHERE Rid = %s", [id])
    menu  = Item.objects.raw("SELECT * FROM item WHERE store = %s", id)
    menus = []
    for i in menu:
        menus.append({"name": i.name,"price": i.price, "desc": i.desc,"pic": static(i.picture)})
    tag = Tag.objects.raw("SELECT t.name FROM tag t JOIN restaurant_tag r ON r.tag_id = t.id WHERE r.restaurant_id = %s;", [id])
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
    "img": static(rest.picture),
    }
    return render(request, "pages.html", {"restaurant": restaurant})

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
    orders = Order.objects.raw("SELECT * FROM 'order' WHERE user_id = %s AND status='completed'", [userid])
    
    UserOrders = []
    for o in orders:
        orderItemsId = o.items.split(",")
        foods = []
        for id in orderItemsId:
            food = list(Item.objects.raw("SELECT * FROM item WHERE id = %s", [id]))[0]
            foods.append({"name":food.name, "price": food.price})
        rest = Restaurant.objects.raw("SELECT name FROM restaurant WHERE Rid = %s", [o.restaurant_id])
        deli = DeliveryP.objects.raw("SELECT u.name FROM delivery_person dp JOIN user u ON dp.user_id = u.user_id WHERE dp.user_id = %s", [o.delivery_person_id])
        ord = {
            "id": o.id,
            "items": foods,
            "price": o.price,
            "created": o.created_at,
            "time": o.time,
            "destination": o.destination,
            "deliveryP": deli,
            "restaurant": rest,   
            "status": o.status, 
        }
        UserOrders.append(ord)
    return render(request, "orders.html", {'order':UserOrders})

def login(request):
    return render(request)


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
        "rest_dest": restaurant_address
    }
    return render(request, "Details.html", {'detail': [details], "deliP": DeliID, "CanTake": True})

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
    Current = Order.objects.raw("SELECT * FROM 'order' WHERE delivery_person_id = %s AND status = 'pending'", [deliID]) 
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
        details = {
        "id": c.id,
        "items": json.dumps(foods),
        "price": c.price,
        "created": c.created_at,
        "restaurant": restaurant_name,
        "customer": customer.name,
        "destination": c.destination,
        "rest_dest": restaurant_address
        }
        CurrentOrders.append(details)

    return render(request, "Details.html", {'detail': CurrentOrders, "deliP": deliID, "CanTake":False})
