from django.urls import path
from django.contrib.auth.decorators import login_required
from . import views

urlpatterns = [
        path('new_account/', views.new_account_view, name='new_account'),
        path('guest/', views.guest_view, name='guest'),
        path('logout/', views.logout_view, name='logout_view'),
        path('', login_required(views.Index_view.as_view()), name="index")
]
