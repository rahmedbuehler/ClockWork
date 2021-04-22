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

# Previous/Next Btns (add week index to get)
# Have calendar expand with available space

class Index_view(View):

    def get_current_week(self, user):
        '''
        Returns the current <Week> object, creating a new <Day> or <Week> if 
        necessary.
        '''
        today = timezone.localdate()
        current_week = user.profile.latest_week
        # New User or new current_week
        if not current_week or today not in current_week.date_list:
            current_week = user.profile.add_week()
        # Current_week exists, but no day object for today
        elif current_week.get_day_list()[today.weekday()] == None:
            current_week.add_day(today)
        return current_week

    def get_week_by_row(self, week, animate=True):
        '''
        Returns a pair with the first element being a list of rows and the second element being a list of
        entry id's to animate.  Each row is a list of length 8 and corresponds to a timeslot from the
        week, starting with the day_start_time and ending with the day_end_time from the user's profile.
        The first entry in each row names the timeslot if it's on the hour (<None> otherwise) while the
        remaining entries correspond to the days of the week (starting with Monday).  Finally, all work
        identifiers are prepended with "color_" and future timeslots with identifier "0" are switched to
        identifier "-1".
        '''
        rows = []
        work_list = week.get_work_list()
        start_hour = week.owner.profile.day_start_time
        end_hour = week.owner.profile.day_end_time
        now = timezone.localtime()
        row_index_cutoff = (now.hour*Day.NUM_BLOCKS_PER_HOUR)+round(now.minute/(60/Day.NUM_BLOCKS_PER_HOUR))-start_hour*Day.NUM_BLOCKS_PER_HOUR
        # Check week to set day cutoff
        day_index_cutoff = timezone.localdate().weekday()
        # Future Week
        if week.date_list[day_index_cutoff] > timezone.localdate():
            day_index_cutoff = -1
        # Past Week
        elif week.date_list[day_index_cutoff] < timezone.localdate():
            day_index_cutoff = 8
        for row_index in range(start_hour*Day.NUM_BLOCKS_PER_HOUR, end_hour*Day.NUM_BLOCKS_PER_HOUR):
            if row_index % Day.NUM_BLOCKS_PER_HOUR == 0:
                row = [week.time_list[row_index//Day.NUM_BLOCKS_PER_HOUR]]
            else:
                row = [None]
            for day_index in range(7):
                if day_index > day_index_cutoff:
                    row.append("color_-1")
                elif day_index == day_index_cutoff and row_index >= row_index_cutoff:
                    row.append("color_-1")
                else:
                    row.append("color_"+work_list[day_index][row_index])
            rows.append(row)

        animate_list = []
        if animate and day_index_cutoff != -1 and day_index_cutoff != 8:
            # Build list of id's for blocks that will be animated and modify rows accordingly.
            i = min(len(rows),row_index_cutoff)-1
            while i > -1 and rows[i][day_index_cutoff] != "color_0":
                animate_list = ["entry_"+str(i)+"_"+str(day_index_cutoff+1)] + animate_list
                rows[i][day_index_cutoff+1] = "color_-1"
                i -= 1
        print("Rows: ",rows)
        print("animate_list: ",animate_list)
        print("now: ", now)
        print("ric: ",row_index_cutoff)
        return rows, animate_list

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
        context["week_by_row"], context["animate_list"] = self.get_week_by_row(current_week)
        context["goal"] = current_week.goal
        context["hours_worked"] = int(round(current_week.get_hours_worked()))
        context["goal_percent"] = round(100*(current_week.get_hours_worked()/current_week.goal),2)
        context["animate_color"]= "color_1"
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
