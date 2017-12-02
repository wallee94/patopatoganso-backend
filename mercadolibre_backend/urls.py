from django.conf.urls import url, include
from django.contrib import admin
import rest_framework.authtoken.views

urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^api/get-token-auth[/]?$', rest_framework.authtoken.views.obtain_auth_token),
    url(r'^api/tracking/', include('tracking.urls')),
]
