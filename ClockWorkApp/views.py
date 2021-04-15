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

# Add Chart
# Add timer
class Index_view(View):

    def get_current_week(self, user):
        today = timezone.localdate()
        current_week = user.profile.latest_week
        # New User or new current_week
        if not current_week or today not in current_week.date_list:
            current_week = user.profile.add_week()
        # current_week exists, but no day object for today
        elif current_week.get_day_list()[today.weekday()] == None:
            current_week.add_day(today)
        return current_week

    def get(self, request):
        context = {}
        # Login as guest if not already authenticated
        if not request.user.is_authenticated:
            user = authenticate(request, username="guest", password=GUEST_PASSWORD)
            if user is not None:
                login(request, user)
        else:
            user = request.user
        # Show login if guest; account name and settings otherwise
        if user.username == "guest":
            context["login_display"] = "show"
            context["user_display"] = "noshow"
        else:
            context["login_display"] = "noshow"
            context["user_display"] = "show"
        current_week = self.get_current_week(user)
        context["date_list"] = [date.strftime("%m/%d") for date in current_week.date_list]
        context["week_by_row"] = current_week.get_week_by_row()
        context["goal"] = current_week.goal
        context["hours_worked"] = int(round(current_week.get_hours_worked()))
        context["goal_percent"] = round(current_week.get_hours_worked()/current_week.goal,2)
        return render(request, "ClockWorkApp/index.html", context)

    def post(self, request):
        if request.POST["start_time"]:
            current_week = self.get_current_week(request.user)
            now = timezone.localtime()
            start_index = request.POST["start_time"].split(":")
            start_index = int(start_index[0])*4+round(int(start_index[-1])/15)
            end_index = now.hour*4+round(now.minute/15)
            if str(timezone.localdate().day) == request.POST["start_day"]:
                current_day = current_week.get_day_list()[timezone.localtime().weekday()]
                current_day.work = current_day.work[0:start_index]+request.POST["work_code"]*(end_index-start_index)+current_day.work[end_index:]
                current_day.save()
            elif str(timezone.localdate().day+1) == request.POST["start_day"]:
                day_2 = Day.objects.filter(week=current_week, date=timezone.localdate()).first()
                # Check for change in week
                if day_2.weekday() == 0:
                    day_1 = current_week.previous.get_day_list()[-1]
                else:
                    day_1 = current_week.get_day_list()[day_2.weekday()-1]
                day_1.work = day_1.work[0:start_index]+request.POST["work_code"]*(96-start_index)
                day_2.work = request.POST["work_code"]*(end_index)+day_2.work[end_index:]
                day_1.save()
                day_2.save()
            return HttpResponseRedirect(reverse("index"))
'''
def new_account_view(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save() username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect(reverse('index'))
    else:
        form = UserCreationForm()
    return render(request, 'ClockWorkApp/new_account.html', {'form': form})
    '''
