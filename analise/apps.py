from django.apps import AppConfig


class AnaliseConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'analise'
    verbose_name = 'Análise de mercado'

    def ready(self):
        # Registra o sinal que tenta geocodificar automaticamente um
        # cliente assim que ele é salvo (ver analise/signals.py).
        from . import signals  # noqa: F401
