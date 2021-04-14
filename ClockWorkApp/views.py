from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import login, authenticate, logout
from django.utils import timezone
from django.views import View
import os
import pytz
GUEST_PASSWORD = os.environ["GUEST_PASSWORD"]

from .models import *

def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse('logout'))

class Index_view(View):
    
    def get(self, request):
        context = {}
        # Login as guest if not already authenticated and show login icon
        if not request.user.is_authenticated:
            user = authenticate(request, username="guest", password=GUEST_PASSWORD)
            context["login_display"] = 'show'
            if user is not None:
                login(request, user)
        else:
            user = request.user
            context["login_display"] = "noshow"
        today = timezone.localdate()
        current_week = user.profile.latest_week
        # New User or new current_week
        if not current_week or today not in current_week.date_list:
            current_week = user.profile.add_week()
        # current_week exists, but no day object for today
        elif current_week.date_list[today.weekday()] == None:
            current_week.add_day(today)
        context["date_list"] = [date.strftime("%m/%d") for date in current_week.date_list]
        context["week_by_row"] = current_week.get_week_by_row()
        context["goal"] = current_week.goal
        context["work_percent"] = current_week.get_hours_worked() / current_week.goal
        return render(request, "ClockWorkApp/index.html", context)
'''
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
    '''
