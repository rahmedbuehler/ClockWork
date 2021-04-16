from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
        path('', views.Index_view.as_view(), name="index"),
]
