from django.shortcuts import get_object_or_404, render, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth import login, authenticate, logout
from django.utils import timezone
from django.views import View
from django.contrib import messages
import os
import pytz

GUEST_PASSWORD = os.environ["GUEST_PASSWORD"]

from .models import *
from .forms import *

# Animation
# Sound
# Flexible row counts
    # Standardize access to indices
    # Make sure profile is read for this
# Make sure start < end on settings/profile

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

    def get(self, request, auth_form=Authentication_Form(), create_form=User_Creation_Form(), settings_form=Settings_Form()):
        context = {"auth_form":auth_form, "create_form":create_form, "settings_form":settings_form}
        # Login as guest if not already authenticated
        if not request.user.is_authenticated:
            user = authenticate(request, username="guest", password=GUEST_PASSWORD)
            if user is not None:
                login(request, user)
        else:
            user = request.user
        # Show login if guest; account name and settings otherwise
        if user.username == "guest":
            context["header_btn_template"] = "ClockWorkApp/login.html"
            context["popup_template"] = "ClockWorkApp/login_popup.html"
        else:
            context["header_btn_template"] = "ClockWorkApp/user.html"
            context["popup_template"] = "ClockWorkApp/settings_popup.html"
        # Settings default to user's profile unless form is bound or None
        if settings_form is not None and not settings_form.is_bound:
            context["settings_form"] = Settings_Form(instance=user.profile)
        # Show popup if any form is bound; if multiple forms, make the bound one visible.
        context["popup_display"] = "noshow"
        context["multi_form_display"] = ["","noshow"]
        if (settings_form is not None and settings_form.is_bound) or (auth_form is not None and auth_form.is_bound):
            context["popup_display"] = ""
        elif create_form is not None and create_form.is_bound:
            context["popup_display"] = ""
            context["multi_form_display"] = ["noshow",""]
        current_week = self.get_current_week(user)
        context["date_list"] = [date.strftime("%m/%d") for date in current_week.date_list]
        context["week_by_row"] = current_week.get_week_by_row()
        context["goal"] = current_week.goal
        context["hours_worked"] = int(round(current_week.get_hours_worked()))
        context["goal_percent"] = round(100*(current_week.get_hours_worked()/current_week.goal),2)
        return render(request, "ClockWorkApp/index.html", context)

    def post(self, request):
        auth_form = None
        create_form = None
        settings_form = None
        # Login Attempt
        if request.POST.get("login",False):
            auth_form = Authentication_Form(request=request, data=request.POST)
            if auth_form.is_valid() and auth_form.user_cache is not None:
                login(request,auth_form.user_cache)
                messages.success(request, 'Success!')
                settings_form = Settings_Form(instance=auth_form.user_cache.profile)
                auth_form = None
            else:
                create_form = User_Creation_Form()
        # Account Creation Attempt
        elif request.POST.get("create", False):
            create_form = User_Creation_Form(request.POST)
            if create_form.is_valid():
                user = create_form.save()
                login(request, user)
                messages.success(request, 'Success!')
                settings_form = Settings_Form(instance=user.profile)
                create_form = None
            else:
                auth_form = Authentication_Form()
        # Modify Settings Attempt
        elif request.POST.get("settings",False):
            settings_form = Settings_Form(instance=request.user.profile, data=request.POST)
            if settings_form.is_valid():
                settings_form.save()
                messages.success(request, 'Success!')
                settings_form = Settings_Form()
        # This added a block
        # Timer Start and Stop
        elif request.POST["start_time"] and request.POST["stop_time"]:
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
            return self.get(request)
        # Shouldn't trigger in normal navigation
        else:
            return self.get(request)
        return self.get(request, auth_form=auth_form, create_form=create_form, settings_form=settings_form)
