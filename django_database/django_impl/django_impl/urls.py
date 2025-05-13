"""
URL configuration for django_impl project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.http import HttpResponse
from django.urls import path
from OrderPage import views # type: ignore
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('index/', views.front ,name='index'),
    path('pages/<int:id>/', views.page, name='pages'),
    path('your_django_cart_view/', views.your_django_cart_view, name='your_django_cart_view'),
    path("cart/", views.view_cart),
    path("contShop/", views.contShop),
    path('vieworder/', views.vieworder),
    path('checkout/', views.checkout, name='checkout'),
    path('orderplaced/', views.orderplaced),
    path('<int:userid>/favorite/', views.fav),
    path("order/<int:userid>", views.orderUser),
    #path("login/", views.login)
    path("deliveryDetails/<int:DeliID>/<int:OrderID>", views.ShowOrderDetails),
    path("takeorder/<int:orderid>/<int:deliID>", views.TakeOrder),
    path('vendor/orders/<int:Rid>', views.vendor_orders_api),
    path('CurrentDelivery/<int:deliID>', views.ShowCurrentOrder),
    path("VendorOrderDetails/<int:Oid>/<int:VendorID>", views.ShowVendorOrder),
    path("PrepareOrder/<int:Oid>", views.PrepOrder),
    path("CompleteOrder/<int:Orderid>/<int:Userid>", views.CompOrder),
    path("UpdateInbox/<int:userid>", views.updateInbox),
    path("Inbox/<int:userid>", views.ViewInbox),
    path("Navi/<int:Oid>", views.StartNav),

    path("login/", views.login_view ,name="login"),

    path("Navi/<int:Oid>", views.StartNav),
    path("AddRestaurant/<int:user>", views.AddRestaurant),
    path("AddMenu/<int:Rid>", views.AddMenuItems),
    path("Menu/<int:user>", views.ViewMenu),
    path("UpdateMenu/<int:ItemId>", views.UpdateStatus),
    path("DeleteMenu/<int:ItemId>", views.deleteItem),
    path("ShowUserCurrentOrder/<int:user>", views.ShowUserCurrent),
    path("Tracker/<int:order>", views.ShowTracker),


    path("Navi/<int:Oid>", views.StartNav),

    path("EditMenu/<int:Mid>", views.UpdateItem),
    path("SearchMenu", views.search)

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)