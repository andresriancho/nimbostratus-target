from fabric.api import task

from servers.django_frontend.deploy import deploy_django_frontend, verify_config
from servers.celery_backend.deploy import deploy_celery_backend
from servers.django_frontend.teardown import teardown_django_frontend
from servers.celery_backend.teardown import teardown_celery_backend

from aws.rds import spawn_rds, teardown_rds
from aws.iam import spawn_iam_user, teardown_iam_user

from core.log_handler import configure_logging


@task
def deploy():
    configure_logging()
    verify_config()
    deploy_django_frontend()
    
    spawn_rds()
    spawn_iam_user()
    
    deploy_celery_backend()

@task
def teardown():
    configure_logging()
    teardown_django_frontend()
    
    teardown_rds()
    teardown_iam_user()
    
    teardown_celery_backend()
    