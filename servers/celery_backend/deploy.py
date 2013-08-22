import time
import logging

from fabric.api import settings, sudo, cd, task, hide
from fabric.contrib.files import upload_template, put

from core.region_connection import EC2Connection
from core.wait_ssh_ready import wait_ssh_ready
from config import AMI, SIZE, DEPLOY_PRIVATE_PATH, DEPLOY_PUBLIC_PATH
from servers.django_frontend.user_data import VULNWEB_REPO, VULNWEB_BRANCH
from aws.keypair import create_keypair
from aws.rds import LOW_PRIV_PASSWORD, LOW_PRIV_USER


NAME = 'celery_backend_nimbostratus'
SG_NAME = '%s_sg' % NAME

SUCCESS_MESSAGE = '''\
You can connect to it via SSH:
    ssh -i celery_backend_nimbostratus.pem ubuntu@%s
'''


@task
def deploy_celery_backend(rds_host, user_key, user_secret):
    '''
    We deploy this celery backend host with the following settings:
        * Has the vulnweb application from django_frontend for running a
          celery worker to consume messages.
        * Has access to the DB 3306 port, where it stores the log messages
        * Has hard-coded AWS credentials to access SQS
        * The credentials have RDS:* , IAM:*, SQS:*
    
    :param rds_host: The RDS instance which we'll use to extract the DB endpoint
    :param user_key: The Amazon API key to hard-code during deployment
    :param user_secret: The Amazon API secret to hard-code during deployment
    '''
    conn = EC2Connection()

    logging.info('Launching Celery backend instance')
    
    logging.debug('    RDS host: %s' % rds_host)
    logging.debug('    Low privilege user access key: %s' % user_key)
    logging.debug('    Low privilege user secret key: %s' % user_secret)
    
    keypair_name = create_keypair(NAME)
    security_group = create_security_group()
    
    my_reservation = conn.run_instances(AMI,
                                        instance_type=SIZE,
                                        key_name=keypair_name,
                                        security_groups=[security_group,],)
 
    instance = my_reservation.instances[0]
    while not instance.update() == 'running':
        logging.debug('Waiting for instance to start...')
        time.sleep(10)

    conn.create_tags([instance.id], {"Name": NAME})
    wait_ssh_ready(instance.public_dns_name)
    
    logging.info('Successfully started %s' % NAME)
    logging.debug(SUCCESS_MESSAGE % instance.public_dns_name)
    
    host_string = 'ubuntu@%s' % instance.public_dns_name
    key_filename = '%s.pem' % NAME
    
    with hide('stdout', 'stderr'):
        with settings(host_string=host_string, key_filename=key_filename,
                      host=instance.public_dns_name):
            setup_celery_backend(rds_host, user_key, user_secret)

def setup_celery_backend(rds_host, user_key, user_secret):
    '''
    The real configuration happens here.
    '''
    logging.info('Updating Ubuntu\'s repository index')
    sudo('apt-get update')
    
    # Not sure why, but sometimes I get "E: Unable to locate package git"
    # trying to solve this with a sleep.
    time.sleep(2)
    sudo('apt-get update')
    
    logging.info('Installing ubuntu packages')
    for pkg in ['git', 'python-pip', 'joe', 'python-mysqldb', 'supervisor']:
        sudo('apt-get install -y -q %s' % pkg)
    
    
    logging.info('Getting celery application source code')
    with cd('/tmp/'):
        sudo('ssh-keyscan -H github.com > /root/.ssh/known_hosts')
        
        put(DEPLOY_PRIVATE_PATH, '/root/.ssh/id_rsa', use_sudo=True)
        put(DEPLOY_PUBLIC_PATH, '/root/.ssh/id_rsa.pub', use_sudo=True)
    
        sudo('chmod 600 /root/.ssh/id_rsa')
        sudo('chmod 600 /root/.ssh/id_rsa.pub')
        
        sudo('git clone %s' % VULNWEB_REPO)
    
    logging.info('Installing requirements.txt (this takes time!)')
    with cd('/tmp/nimbostratus-target/'):
        sudo('git checkout %s' % VULNWEB_BRANCH)
        sudo('pip install --use-mirrors --upgrade -r requirements.txt')

    vulnweb_root = '/tmp/nimbostratus-target/servers/django_frontend/vulnweb'

    logging.info('Configuring django-celery application')
    # Overwrite the application configuration files
    upload_template('servers/celery_backend/broker.config',
                    '%s/vulnweb/broker.py' % vulnweb_root,
                    context={'access': user_key,
                             'secret': user_secret},
                    backup=False, use_sudo=True)

    upload_template('servers/celery_backend/databases.config',
                    '%s/vulnweb/databases.py' % vulnweb_root,
                    context={'user': LOW_PRIV_USER,
                             'password': LOW_PRIV_PASSWORD,
                             'host': rds_host},
                    backup=False, use_sudo=True)

    upload_template('servers/celery_backend/supervisor.config',
                    '/etc/supervisor/conf.d/celery.conf',
                    context={'django_root_path': vulnweb_root},
                    backup=False, use_sudo=True)

    sudo('supervisorctl update')
    
    with cd(vulnweb_root):
        sudo('python manage.py syncdb --noinput')

def create_security_group(): 
    conn = EC2Connection()
    
    for sg in conn.get_all_security_groups():
        if sg.name == SG_NAME:
            return SG_NAME
         
    web = conn.create_security_group(SG_NAME, 'Allow port 22.')
    web.authorize('tcp', 22, 22, '0.0.0.0/0')
    
    return SG_NAME