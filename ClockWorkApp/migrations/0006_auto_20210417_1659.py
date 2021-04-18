# Generated by Django 2.2.12 on 2021-04-17 16:59

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ClockWorkApp', '0005_profile_default_goal'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='day_end_time',
            field=models.PositiveSmallIntegerField(choices=[(0, '12am'), (1, '1am'), (2, '2am'), (3, '3am'), (4, '4am'), (5, '5am'), (6, '6am'), (7, '7am'), (8, '8am'), (9, '9am'), (10, '10am'), (11, '11am'), (12, '12pm'), (13, '1pm'), (14, '2pm'), (15, '3pm'), (16, '4pm'), (17, '5pm'), (18, '6pm'), (19, '7pm'), (20, '8pm'), (21, '9pm'), (22, '10pm'), (23, '11pm')], default=22, validators=[django.core.validators.MaxValueValidator(23)]),
        ),
        migrations.AlterField(
            model_name='profile',
            name='day_start_time',
            field=models.PositiveSmallIntegerField(choices=[(0, '12am'), (1, '1am'), (2, '2am'), (3, '3am'), (4, '4am'), (5, '5am'), (6, '6am'), (7, '7am'), (8, '8am'), (9, '9am'), (10, '10am'), (11, '11am'), (12, '12pm'), (13, '1pm'), (14, '2pm'), (15, '3pm'), (16, '4pm'), (17, '5pm'), (18, '6pm'), (19, '7pm'), (20, '8pm'), (21, '9pm'), (22, '10pm'), (23, '11pm')], default=4, validators=[django.core.validators.MaxValueValidator(23)]),
        ),
    ]
