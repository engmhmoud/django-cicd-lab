from django.urls import path

from orders import views

urlpatterns = [
    path("healthz", views.healthz),
    path("readyz", views.readyz),
    path("version", views.version),
    path("api/orders", views.orders),
    path("api/orders/<uuid:order_id>", views.order_detail),
]
