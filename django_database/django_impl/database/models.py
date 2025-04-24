from django.db import models
from datetime import timedelta

def default_duration():
    return timedelta(0)

class User(models.Model):
    user_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    


    class Meta:
        db_table = "user"

class Customer(User):
    favorite_restaurants = models.ManyToManyField(
        'Restaurant',
        through='Favorite',
        related_name='favored_by'
    )
    class Meta:
        db_table = "customer"

class DeliveryP(User):
    miles = models.IntegerField(default=0)
    last_delivery_time = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "delivery_person"

class Restaurant(models.Model):
    Rid = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    picture = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=100, default="-")
    desc = models.TextField(default="-")
    class Meta:
        db_table = "restaurant"

class Vendor(User):
    store = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='vendors')

    class Meta:
        db_table = "vendor"

class Favorite(models.Model):
    user = models.ForeignKey(Customer, on_delete=models.CASCADE)
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('user', 'restaurant')
        db_table = "favorite"

class FreqAddr(models.Model):
    user = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='frequent_addresses')
    address = models.CharField(max_length=100)

    class Meta:
        unique_together = ('user', 'address')
        db_table = "frequent_address"

class Tag(models.Model):
    name = models.CharField(max_length=100) 

    class Meta:
        db_table = "tag"

class RestaurantTag(models.Model):
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('restaurant', 'tag')
        db_table = "restaurant_tag"

class Item(models.Model):
    store = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    desc = models.TextField()
    picture = models.CharField(max_length=100, blank=True)

    class Meta:
        db_table = "item"

class Order(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='orders')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE)
    delivery_person = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deliveries')
    items = models.CharField(max_length=100)  # Could later become ManyToMany if needed
    price = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=100, default="Pending")
    destination = models.CharField(max_length=100, default="-")
    time = models.DurationField(default=default_duration)

    class Meta:
        db_table = "order"
