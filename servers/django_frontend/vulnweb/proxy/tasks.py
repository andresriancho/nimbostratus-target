from celery import task
from models import Log


@task()
def log_url(url):
    log = Log.objects.create(url=url)
    log.save()

