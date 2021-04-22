from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.conf import settings
from django.utils.functional import cached_property
import datetime
import pytz

class User(AbstractUser):
    pass

class Week (models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="days", on_delete = models.CASCADE)
    goal = models.PositiveSmallIntegerField(default=40, validators=[MinValueValidator(0), MaxValueValidator(168)])
    previous = models.OneToOneField("self", related_name="next", on_delete = models.SET_NULL, null=True, blank=True)

    @cached_property
    def time_list (self):
        return ["12am"]+[str(i)+"am" for i in range(1,12)] + ["12pm"] + [str(i)+"pm" for i in range(1,12)]

    @cached_property
    def date_list (self):
        if not self.days.exists():
            raise Exception("date_list called on an empty week\n")
        i = 0
        date_list = []
        days_index = 0
        days = self.days.order_by("date")
        while i < 7:
            if days_index < len(days) and days[days_index].date.weekday() == i:
                date_list.append(days[days_index].date)
                days_index += 1
            else:
                date_list.append(days[0].date + datetime.timedelta(days=(i - days[0].date.weekday())))
            i+=1
        if len(date_list) != 7:
            raise Exception(f"date_list returned a list with the incorrect length, {date_list}\n")
        return date_list

    def get_day_list (self):
        if not self.days.exists():
            return [None]*7
        i = 0
        day_list = []
        days_index = 0
        days = self.days.order_by("date")
        while i < 7:
            if days_index < len(days) and days[days_index].date.weekday() == i:
                day_list.append(days[days_index])
                days_index += 1
            else:
                day_list.append(None)
            i+=1
        if len(day_list) != 7:
            raise Exception(f"get_day_list returned a list with the incorrect length, {day_list}\n")
        return day_list

    def get_work_list(self):
        work_list = []
        for day in self.get_day_list():
            if day != None:
                work_list.append(day.work)
            else:
                work_list.append("0"*96)
        return work_list

    def get_hours_worked(self):
        hours = 0
        for day in self.get_work_list():
            for timeslot in day:
                if timeslot > "0":
                    hours += .25
        return hours

    def add_day (self, date):
        day = Day.objects.create(date=date, week=self)

@receiver(pre_delete, sender=Week)
def update_links (sender, instance, **kwargs):
    # Update previous/next pointers
    if instance.previous and hasattr(instance,"next"):
        instance.next.previous = instance.previous
        instance.next.previous.save()
    # Update latest week pointer
    if instance.owner.profile and instance.previous:
        instance.owner.profile.latest_week = instance.previous
        instance.owner.profile.save()

class Day (models.Model):
    NUM_BLOCKS_PER_HOUR = 4
    date = models.DateField()
    work = models.CharField(max_length=NUM_BLOCKS_PER_HOUR*24, default = "0"*(NUM_BLOCKS_PER_HOUR*24), validators=[RegexValidator(regex='^\d{'+str(NUM_BLOCKS_PER_HOUR*24)+'}$', message='Length has to be NUM_BLOCKS_PER_HOUR * 24 hours', code='nomatch')])
    week = models.ForeignKey(Week, related_name="days", on_delete = models.CASCADE)

class Profile (models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    latest_week = models.OneToOneField(Week, on_delete = models.SET_NULL, null=True, blank=True)
    TIMEZONE_CHOICES = tuple(zip(pytz.common_timezones, pytz.common_timezones))
    timezone = models.CharField(max_length=32, choices=TIMEZONE_CHOICES, default="UTC")
    TIMES = ["12am"]+[str(i)+"am" for i in range(1,12)]+["12pm"]+[str(i)+"pm" for i in range(1,12)]+["12am"]
    TIME_CHOICES = tuple(zip(range(0,25),TIMES))
    # Start and end hour (0-24) with 12am appearing as both 0 and 24
    day_start_time = models.PositiveSmallIntegerField(choices=TIME_CHOICES, default=4, validators=[MaxValueValidator(24)])
    day_end_time = models.PositiveSmallIntegerField(choices=TIME_CHOICES, default=22, validators=[MaxValueValidator(24)])
    default_goal = models.PositiveSmallIntegerField(default=40, validators=[MinValueValidator(0), MaxValueValidator(168)])

    def add_week(self):
        new_week = Week.objects.create(owner=self.user, previous=self.latest_week)
        Day.objects.create(date=timezone.localdate(), week=new_week)
        self.latest_week = new_week
        new_week.goal = self.default_goal
        self.save()
        return new_week

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()
