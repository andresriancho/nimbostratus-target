import sys
import requests
import os
import time
import logging

from core.region_connection import EC2Connection
from config import AMI, SIZE, DEPLOY_PRIVATE_PATH, DEPLOY_PUBLIC_PATH
from aws.keypair import create_keypair
from aws.ec2 import create_instance_profile

TEST_URL = 'http://%s/?url=http://httpbin.org/user-agent'
NAME = 'django_frontend_nimbostratus'
SG_NAME = '%s_sg' % NAME
SQS_POLICY = """{
  "Statement":[{
    "Effect":"Allow",
    "Action":["sqs:*"],
    "Resource": "*"}]}
"""
SUCCESS_MESSAGE = '''\
You can connect to it via SSH and HTTP:
    http://%s/
    http://%s/?url=http://httpbin.org/user-agent
    
    ssh -i django_frontend_nimbostratus.pem ubuntu@%s
'''

def deploy_django_frontend():
    conn = EC2Connection()

    logging.info('Launching Django frontend instance')
    
    keypair_name = create_keypair(NAME)
    user_data = get_user_data()
    security_group = create_security_group()
    instance_profile = create_instance_profile(NAME, SQS_POLICY)
    
    my_reservation = conn.run_instances(AMI,
                                        instance_type=SIZE,
                                        key_name=keypair_name,
                                        user_data=user_data,
                                        security_groups=[security_group,],
                                        instance_profile_name=instance_profile)
 
    instance = my_reservation.instances[0]
    while not instance.update() == 'running':
        logging.debug('Waiting for instance to start...')
        time.sleep(10)

    logging.info('Checking if instance was correctly configured (this usually takes 5min)')
    
    conn.create_tags([instance.id], {"Name": NAME})
    
    for _ in xrange(10):
        
        time.sleep(60)
        
        try:
            response = requests.get(TEST_URL % instance.public_dns_name)
        except Exception:
            logging.debug('Instance did not boot yet...')
        else:
            assert 'python-requests' in response.text, 'Incorrectly configured!'
            break
    else:
        raise Exception('Timeout! Instance failed to boot.')
    
    logging.info('Successfully started %s' % NAME)
    logging.debug(SUCCESS_MESSAGE % (instance.public_dns_name,
                                     instance.public_dns_name,
                                     instance.public_dns_name))

def create_security_group(): 
    conn = EC2Connection()
    
    for sg in conn.get_all_security_groups():
        if sg.name == SG_NAME:
            return SG_NAME
         
    web = conn.create_security_group(SG_NAME, 'Allow ports 80 and 22.')
    web.authorize('tcp', 80, 80, '0.0.0.0/0')
    web.authorize('tcp', 22, 22, '0.0.0.0/0')
    
    return SG_NAME

def get_user_data():
    '''
    :return: A string which contains the user_data.py file contents with the
             replaced variables.
    '''
    user_data = file('servers/django_frontend/user_data.py').read()
    
    user_data = user_data.replace('__VULNWEB_DEPLOY_PRIVATE_KEY__',
                                  file(DEPLOY_PRIVATE_PATH).read())
    user_data = user_data.replace('__VULNWEB_DEPLOY_PUBLIC_KEY__',
                                  file(DEPLOY_PUBLIC_PATH).read())
    
    return user_data

def verify_config():
    if not os.path.exists(DEPLOY_PRIVATE_PATH) or not \
    os.path.exists(DEPLOY_PUBLIC_PATH):
        logging.critical('You need to setup your Github repository with'\
                         ' SSH deploy keys and set the path to those files'
                         ' in the config.py file. See: https://help.github.com/articles/managing-deploy-keys')
        sys.exit(1)


