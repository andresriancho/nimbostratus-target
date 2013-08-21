from celery import task

@task()
def log_url(url):
    return url
