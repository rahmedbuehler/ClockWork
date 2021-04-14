from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
        path('logout/', views.logout_view, name='logout_view'),
        path('', views.Index_view.as_view(), name="index"),
]
