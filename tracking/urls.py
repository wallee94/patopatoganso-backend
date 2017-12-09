from django.conf.urls import url
from .views import PriceAPIVIew

urlpatterns = [
    url(r'^prices[/]?$', PriceAPIVIew.as_view()),
]
