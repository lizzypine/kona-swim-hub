# Generated by Django 4.1.2 on 2022-10-21 05:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("lessons", "0011_remove_course_num_spots_available"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="course",
            name="learner_on_roster",
        ),
    ]
