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
        # Login as guest if not already authenticated and show login icon
        if not request.user.is_authenticated:
            user = authenticate(request, username="guest", password=GUEST_PASSWORD)
            context["login_display"] = 'show'
            if user is not None:
                login(request, user)
        else:
            user = request.user
            context["login_display"] = "noshow"
        # New User or new week
        today = datetime.date.today()
        if not user.profile.latest_week or today not in user.profile.latest_week.date_list:
            current_week = user.profile.add_week()
        # Week exists, but no day object for today
        elif current_week.date_list[today.weekday()] == None:
            current_week.add_day(today)
        context["date_list"] = current_week.date_list
        context["work_list"] = current_week.get_work_list()
        context["today"] = today.weekday()
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
