from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

class SendemailConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "sendemail"
