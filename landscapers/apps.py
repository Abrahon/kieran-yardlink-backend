from django.apps import AppConfig


class LandscapersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'landscapers'

    def ready(self):
        import landscapers.signals


    
