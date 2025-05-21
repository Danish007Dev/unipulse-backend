from django.apps import AppConfig


class UniappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'uniapp'



    def ready(self):
        import uniapp.signals  # 👈 import signals so they get registered