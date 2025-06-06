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
    path("SearchMenu", views.search),
    path("GetHeatMap/<int:Oid>", views.heatmap),
    path("GetCurrentCoords/<int:Oid>", views.getCoords),
    path("DeliveryEstimate/", views.startEstimate),
    path("AreaEstimate/<str:area>", views.AreaEstimate),
    path("GetCity/<int:Oid>", views.getCity),
    path("AreaEstimateDeli/<str:area>/<int:Oid>", views.AreaEstimateDeli),
    path("rateOrder/<int:Oid>/<int:Uid>", views.RateOrder),
    path("ProcessOrder/<int:Oid>/<int:score>/<str:comment>", views.ProcessOrder),
    path("Rankings/", views.Rankings),
    path("CheckAlreadyReviewed/<int:Oid>", views.checkReviewed),
    path("SearchRestaurantsWithTag/", views.SearchRest),
    path("GetInbox/<int:userid>", views.GetInbox),
    path("AccountInfo/<int:userid>/<str:role>", views.GetAccount),
    path("UpdateAccountInfo/<int:userid>/<str:role>", views.updateAccount),
    path("DeleteRestaurant/<int:userid>/<int:rest>", views.DeleteRest),
    path("DeleteInbox/<int:Mid>", views.DelMsg),
    path("GetOrderByDate/<str:date>/<int:user>", views.GetByDate),
    path('fvrclick/', views.addFvr),
    path('remclick/', views.remFvr),
    path('vieworder/', views.vieworder),
    path('checkout/', views.checkout, name='checkout'),
    path("SearchFavoriteRestaurantsWithTag/<int:user>", views.SearchFavRest),
    path("SearchDelivery/", views.searchDelivery),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)



if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)