from django.conf.urls import url
from . import views

urlpatterns = [
    url(r'^get_message/$', views.get_message, name='get_message'),
    url(r'^callback', views.get_code, name='get_code'),
    url(r'^get_url/$', views.get_url, name='get_url')
]
