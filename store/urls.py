from django.urls import path

from .views import buy_product 
from .views import buy_atomic
from .views import buy_f



urlpatterns = [
    path(
        'buy/<int:product_id>/',
      
        buy_product
    
    ),
    path(
        'buy/a/<int:product_id>/',
        buy_atomic
    ),


    path('buy-f/<int:product_id>/', buy_f),
    


]
