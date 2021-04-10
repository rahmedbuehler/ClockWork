from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.models import AbstractUser
from django.conf import settings

class User(AbstractUser):
    pass

class Day (models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, related_name="days", on_delete = models.CASCADE)
    date = models.DateField()
    work = models.CharField(max_length=96, default = "0"*96, validators=[RegexValidator(regex='^\d{96}$', message='Length has to be 96 (4 fifteen minute blocks per hour * 24 hours)', code='nomatch')])
