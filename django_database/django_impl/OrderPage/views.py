from django.shortcuts import render
from django.templatetags.static import static
from database.models import Customer, Vendor, DeliveryP, Favorite,RestaurantTag, Tag, Item, Restaurant, Order # type: ignore
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
    test_user = Vendor.objects.first()
    #user = request.user
    role = None
    if hasattr(test_user, 'customer'):
        role = 'customer'
    elif hasattr(test_user, 'vendor'):
        role = 'vendor'
    elif hasattr(test_user, 'delivery'):
        role = 'delivery'
    
    if role == 'vendor':
        pending = Order.objects.raw("SELECT * FROM 'order' WHERE restaurant_id = %s and status = 'pending'", [test_user.store])
        order_inc = []
        for o in pending:
            itemId = o.items.split(",")
            itms = []
            for i in itemId:
                item = Item.objects.raw("SELECT * FROM item WHERE id = %s", [i])
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
                "customer": o.user_id,
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
    orders = Order.objects.raw("SELECT * FROM 'order' WHERE user_id = %s", [userid])
    
    UserOrders = []
    for o in orders:
        orderItemsId = o.items.split(",")
        foods = []
        for id in orderItemsId:
            food = Item.objects.raw("SELECT * FROM item WHERE id = %s", [id])
            foods.append({"name":food.name, "price": food.price})
        rest = Restaurant.objects.raw("SELECT name FROM restaurant WHERE Rid = %s", [o.restaurant_id])
        deli = DeliveryP.objects.raw("SELECT u.name FROM delivery_person dp JOIN user u ON dp.user_id = u.user_id WHERE dp.user_id = %s", [o.delivery_person_id])
        ord = {
            "id": o.id,
            "items": foods,
            "price": o.price,
            "created": o.created_at,
            "deliveryP": deli,
            "restaurant": rest,    
        }
        UserOrders.append(ord)
    return render(request, "orders.html", {'order':UserOrders})


