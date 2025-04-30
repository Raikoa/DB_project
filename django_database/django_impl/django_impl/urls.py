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

urlpatterns = [
    path('admin/', admin.site.urls),
    path('index/', views.front),
    path('pages/<int:id>/', views.page, name='pages'),
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
    path("Navi/<int:Oid>", views.StartNav)
]
