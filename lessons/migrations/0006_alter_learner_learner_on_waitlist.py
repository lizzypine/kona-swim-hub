# Generated by Django 4.0.5 on 2022-09-13 01:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('lessons', '0005_alter_waitlist_listed_on_waitlist'),
    ]

    operations = [
        migrations.AlterField(
            model_name='learner',
            name='learner_on_waitlist',
            field=models.ManyToManyField(default=None, null=True, related_name='waitlists', to='lessons.waitlist'),
        ),
    ]
