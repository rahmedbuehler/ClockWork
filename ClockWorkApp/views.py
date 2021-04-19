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

# Slot fill animation
# Stopwatch animation
# Sound
# Standardize access to indices and num blocks per hour
# Previous/Next Btns (add index to get)
# Make POST not reset timer
# Make timer inputs use form

class Index_view(View):

    def get_current_week(self, user):
        today = timezone.localdate()
        current_week = user.profile.latest_week
        # New User or new current_week
        if not current_week or today not in current_week.date_list:
            current_week = user.profile.add_week()
        # Current_week exists, but no day object for today
        elif current_week.get_day_list()[today.weekday()] == None:
            current_week.add_day(today)
        return current_week

    def get_week_by_row(self, week):
        '''
        Returns a 96 by 8 list of lists where each of the 96 rows corresponds to a timeslot from the week.
        The first entry in each row names the timeslot if it's on the hour (<None> otherwise) while the
        remaining entries correspond to the days of the week (starting with Monday).  Finally, all work
        identifiers are prepended with "color_" and future timeslots with identifier "0" are switched to
        identifier "-1".
        '''
        rows = []
        work_list = week.get_work_list()
        row_index_cutoff = (timezone.localtime().hour*4)+round(timezone.localtime().minute/15)
        # Current Week
        day_index_cutoff = timezone.localdate().weekday()
        # Future Week
        if week.date_list[day_index_cutoff] > timezone.localdate():
            day_index_cutoff = -1
        # Past Week
        elif week.date_list[day_index_cutoff] < timezone.localdate():
            day_index_cutoff = 8
        for row_index in range(96):
            if row_index % 4 == 0:
                row = [week.time_list[row_index//4]]
            else:
                row = [None]
            for day_index in range(7):
                if day_index > day_index_cutoff and work_list[day_index][row_index] == "0":
                    row.append("color_-1")
                elif day_index == day_index_cutoff and row_index >= row_index_cutoff and work_list[day_index][row_index] == "0":
                    row.append("color_-1")
                else:
                    row.append("color_"+work_list[day_index][row_index])
            rows.append(row)
        return rows

    def get(self, request, auth_form=Authentication_Form(), create_form=User_Creation_Form(), settings_form=Settings_Form()):
        context = {"timer_form": Timer_Form(), "auth_form":auth_form, "create_form":create_form, "settings_form":settings_form}
        # Login as guest if not already authenticated
        if not request.user.is_authenticated:
            user = authenticate(request, username="guest", password=GUEST_PASSWORD)
            if user is not None:
                login(request, user)
        else:
            user = request.user
        # Show login if guest; account name and settings icon otherwise
        if user.username == "guest":
            context["header_btn_template"] = "ClockWorkApp/login.html"
            context["popup_template"] = "ClockWorkApp/login_popup.html"
        else:
            context["header_btn_template"] = "ClockWorkApp/user.html"
            context["popup_template"] = "ClockWorkApp/settings_popup.html"
        # Settings are set to user's profile unless form is bound
        if settings_form is None or not settings_form.is_bound:
            context["settings_form"] = Settings_Form(instance=user.profile)
        # Show popup if any form is bound; if multiple forms on the page, make the bound one visible.
        context["popup_display"] = "noshow"
        context["multi_form_display"] = ["","noshow"]
        if context["settings_form"].is_bound or (auth_form is not None and auth_form.is_bound):
            context["popup_display"] = ""
        elif create_form is not None and create_form.is_bound:
            context["popup_display"] = ""
            context["multi_form_display"] = ["noshow",""]
        # Set standard display elements
        current_week = self.get_current_week(user)
        context["date_list"] = [date.strftime("%m/%d") for date in current_week.date_list]
        NUM_BLOCKS_PER_HOUR = 4
        context["week_by_row"] = self.get_week_by_row(current_week)[NUM_BLOCKS_PER_HOUR*user.profile.day_start_time:NUM_BLOCKS_PER_HOUR*user.profile.day_end_time]
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
                auth_form = None
            else:
                create_form = User_Creation_Form()
        # Account Creation Attempt
        elif request.POST.get("create", False):
            create_form = User_Creation_Form(request.POST)
            if create_form.is_valid():
                user = create_form.save()
                login(request, user)
                create_form = None
            else:
                auth_form = Authentication_Form()
        # Modify Settings Attempt
        elif request.POST.get("settings", False):
            settings_form = Settings_Form(instance=request.user.profile, data=request.POST)
            if settings_form.is_valid():
                settings_form.save()
                settings_form = None
        # Timer Start and Stop
        elif request.POST.get("work_time", False):
            timer_form = Timer_Form(data=request.POST)
            if timer_form.is_valid():
                current_week = self.get_current_week(request.user)
                end = timezone.localtime()
                start = end - timezone.timedelta(seconds=timer_form.cleaned_data["work_time"])
                start_index = start.hour*4+round(start.minute/15)
                end_index = end.hour*4+round(end.minute/15)
                # Same day
                if start.day == end.day:
                    current_day = current_week.get_day_list()[timezone.localtime().weekday()]
                    current_day.work = current_day.work[0:start_index]+request.POST["work_code"]*(end_index-start_index)+current_day.work[end_index:]
                    current_day.save()
                # Next day
                elif start.day +1 == end.day:
                    day_2 = Day.objects.filter(week=current_week, date=end.date()).first()
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
