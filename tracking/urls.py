from django.conf.urls import url
from .views import PriceAPIVIew, KeywordAPIView

urlpatterns = [
    url(r'^prices/$', PriceAPIVIew.as_view()),
    url(r'^keywords/$', KeywordAPIView.as_view()),
]
