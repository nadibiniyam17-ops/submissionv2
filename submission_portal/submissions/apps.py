from django.apps import AppConfig
from django.db.backends.signals import connection_created


def configure_sqlite(sender, connection, **kwargs):
    if connection.vendor != 'sqlite':
        return
    with connection.cursor() as cursor:
        cursor.execute('PRAGMA journal_mode=WAL;')
        cursor.execute('PRAGMA busy_timeout=30000;')
        cursor.execute('PRAGMA synchronous=NORMAL;')
        cursor.execute('PRAGMA foreign_keys=ON;')


class SubmissionsConfig(AppConfig):
    name = 'submissions'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        connection_created.connect(
            configure_sqlite,
            dispatch_uid='submissions.configure_sqlite',
        )
