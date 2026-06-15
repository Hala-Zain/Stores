from functools import wraps
from django.core.cache import cache


def track_product_view(view_func):

    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        product_id = kwargs.get("id")
        if product_id:
            key = f"product_views:{product_id}"
            current_views = cache.get(key,0)
            cache.set(key,current_views + 1)
            print(
                f"PRODUCT {product_id} VIEWS = {current_views + 1}"
            )
        return view_func(request,*args,**kwargs)
    return wrapper