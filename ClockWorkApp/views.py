from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import login, authenticate, logout
from django.utils import timezone
from django.views import View
import datetime
import os
GUEST_PASSWORD = os.environ["GUEST_PASSWORD"]

from .models import *

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('logout'))

def guest_view(request):
    username = 'guest'
    user = authenticate(request, username=username, password=GUEST_PASSWORD)
    if user is not None:
        login(request, user)
        return HttpResponseRedirect(reverse('index'))

class Index_view(View):
    
    def get(self, request):
        context = {}
        context["times"] = [str(i)+"am" for i in range(5,12)] + ["12pm"] + [str(i)+"pm" for i in range(1,12)] + ["12am"] + [str(i)+"am" for i in range(1,5)]
        if not request.user.is_authenticated:
            user = authenticate(request, username="guest", password=GUEST_PASSWORD)
            if user is not None:
                login(request, user)
        days = list(Day.objects.filter(owner=request.user).order_by('-date'))
        if not days:
            days = [Day.objects.create(owner=request.user, date=datetime.date.today())]
        return render(request, "ClockWorkApp/index.html", context)

def new_account_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect(reverse('index'))
    else:
        form = UserCreationForm()
    return render(request, 'ClockWorkApp/new_account.html', {'form': form})
