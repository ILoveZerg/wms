from django.urls import path
from . import views
from .views import ItemView, TransferView, PullView, PutAwayView

urlpatterns = [
    path("items/", ItemView.as_view(), name='items'),
    path("transfers/", TransferView.as_view(), name='transfers'),
    path("upload/", views.upload_data, name='upload_data'),
    path("pull/", PullView.as_view(), name='pull'),
    path("put_away/", PutAwayView.as_view(), name='put_away')
]
"""
    path("items/<str:search_term>/", views.item_search),
    path("items/<str:item>/", views.item_detail),
    path("transfers/", views.transfers),
    path("transfers/<str:search_term>/", views.transfer_search),
    path("transfers/<str:transfer>/", views.transfer_detail),
    path("transfers/<str:transfer>/<str:scan>/", views.transfer_item_scanned),
    path("transfers/<str:transfer>/start/", views.start_transfer),
    path("transfers/<str:transfer>/finish/", views.finish_transfer),
    path("transfers/<str:transfer>/send/", views.send_transfer),
    path("purchase_orders/", views.purchase_orders),
    path("purchase_orders/<str:search_term>/", views.purchase_order_search),
    path("purchase_orders/<str:purchase_order>/", views.purchase_order_detail),
    path("purchase_orders/<str:purchase_order>/start/", views.check_in_purchase_order),
    path("purchase_orders/<str:purchase_order>/<str:scan>/", views.purchase_order_scanned)
    """