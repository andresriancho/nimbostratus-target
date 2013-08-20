#!/usr/bin/python

#
# REMINDER: You're on a new box. Empty. Nothing is installed but python.
#
import logging
import subprocess
import os
import shlex
import time

from datetime import timedelta

LOG_FILE = '/var/log/cloud-user-data.log'

# Where to get the code from
VULNWEB_REPO = 'git@github.com:andresriancho/nimbostratus-target.git'
VULNWEB_BRANCH = 'master'

NGINX_CONFIG = '''\
upstream django {
    # Unix sockets have less overhead than TCP sockets
    server unix:///tmp/vulnweb.sock;
}

server {
    listen      80;

    # Send all requests to the Django server.
    location / {
        uwsgi_pass  django;
        include     /etc/nginx/uwsgi_params;
    }
}
'''

UWSGI_CONFIG = '''\
[uwsgi]

chdir           = /var/www/vulnweb/
module          = vulnweb.wsgi

# process-related settings
# master
master          = true
processes       = 10
socket          = /tmp/vulnweb.sock
chmod-socket    = 664
vacuum          = true
daemonize = /var/log/vulnweb.log
'''

# How to access the code
VULNWEB_DEPLOY_PRIVATE_KEY = '''\
__VULNWEB_DEPLOY_PRIVATE_KEY__'''
VULNWEB_DEPLOY_PUBLIC_KEY = '''\
__VULNWEB_DEPLOY_PUBLIC_KEY__'''

# Package stuff
APT_INSTALL = 'apt-get install -y -q %s'
PACKAGES = ['git', 'python-pip', 'nginx']


def configure_logging():
    
    log_file = file(LOG_FILE, 'w')
    log_file.write('')
    log_file.close()
    
    os.chmod(LOG_FILE, 0600)

    # Use syslog format
    syslog_format = '%(asctime)s deploy cloud-init: %(levelname)s: %(message)s'    
    
    logging.basicConfig(filename=LOG_FILE,
                        format=syslog_format,
                        datefmt='%b %d %H:%M:%S',
                        filemode='w',
                        level=logging.DEBUG)
    
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.DEBUG)
    logging.getLogger('').addHandler(console)

def run_cmd(cmd, shell=False, cwd=None):
    logging.info('Running "%s"' % cmd)
    
    args = shlex.split(cmd)
    
    process = subprocess.Popen(args,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.STDOUT,
                               shell=shell,
                               universal_newlines=True,
                               cwd=cwd)

    result = ''
    
    while True:
        line = process.stdout.readline()
        if not line:
            break
        
        logging.debug(line.strip())
        result += line
    
    process.wait()
    if process.returncode != 0:
        logging.error('%s finished with return code %s' % (cmd,
                                                           process.returncode))
        
    return result, process.returncode
    
def install_prerequisites():
    logging.info('Installing prerequisites for user_data script.')
    run_cmd('apt-get update -y -q')
    
    for pkg in PACKAGES:
        run_cmd(APT_INSTALL % pkg)

def setup_keys(private, public):
    logging.info('Setting SSH keys as default')
    
    # I am...
    file('/root/.ssh/id_rsa', 'w').write(private)
    file('/root/.ssh/id_rsa.pub', 'w').write(public)
    
    run_cmd('chmod 600 /root/.ssh/id_rsa')
    run_cmd('chmod 600 /root/.ssh/id_rsa.pub')
    
    # Github is...
    key, _ = run_cmd('ssh-keyscan -H github.com')
    file('/root/.ssh/known_hosts', 'w').write(key.strip())

def remove_keys():
    logging.info('Removing user-data deploy SSH keys')
    run_cmd('rm -rf /root/.ssh/id_rsa')
    run_cmd('rm -rf /root/.ssh/id_rsa.pub')


def setup_vulnweb():
    '''
    Perform these main actions:
        * Clone the repository
        * Configure Nginx and uwsgi
    '''
    clone_repository()
    copy_vulnweb_to_var_www()
    configure_uwsgi()
    configure_nginx()    

def copy_vulnweb_to_var_www():
    src = 'servers/django_frontend/vulnweb'
    dst = '/var/www/'
    run_cmd('cp -rf %s %s' % (src, dst), cwd='nimbostratus-target')

def configure_nginx():
    config = file('/etc/nginx/sites-enabled/vulnweb', 'w')
    config.write(NGINX_CONFIG)
    config.close()
    
    run_cmd('sudo /etc/init.d/nginx restart')

def configure_uwsgi():
    config = file('/tmp/uwsgi.ini', 'w')
    config.write(UWSGI_CONFIG)
    config.close()
    
    run_cmd('sudo uwsgi --ini /tmp/uwsgi.ini')

def clone_repository():
    logging.info('Cloning repository')
    setup_keys(VULNWEB_DEPLOY_PRIVATE_KEY, VULNWEB_DEPLOY_PUBLIC_KEY)
    
    run_cmd('git clone %s nimbostratus-target' % VULNWEB_REPO)
    run_cmd('git checkout %s' % VULNWEB_BRANCH, cwd='nimbostratus-target')
    run_cmd('pip install --use-mirrors --upgrade -r requirements.txt',
            cwd='nimbostratus-target')
    
    remove_keys()

        
if __name__ == '__main__':
    start_time = time.time()
    configure_logging()
    
    # Reminder: from a run in Ubuntu 12.04.2 I get the following:
    # Current working directory is: /
    logging.debug('Current working directory is: %s' % os.getcwd())
    logging.debug('Script located at: %s' % __file__)
    
    install_prerequisites()
    
    try:
        setup_vulnweb()
    except Exception, e:
        logging.critical('User data script exception: "%s"' % e)
    finally:
        remove_keys()
    
    end_time = time.time()
    run_time = timedelta(seconds=end_time-start_time)
    logging.debug('Total deploy time: %s' % run_time)