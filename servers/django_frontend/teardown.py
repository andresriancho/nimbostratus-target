import logging

from core.region_connection import EC2Connection

from aws.ec2 import terminate_instance, get_instances_to_terminate, delete_instance_profile
from servers.django_frontend.deploy import NAME, SG_NAME


def teardown_django_frontend():
    for inst in get_instances_to_terminate(NAME):
        terminate_instance(inst)

    logging.debug('Removing keypair "%s"' % NAME)        
    conn = EC2Connection()
    conn.delete_key_pair(NAME)

    logging.debug('Removing security group "%s"' % NAME)
    conn.delete_security_group(SG_NAME)
    
    delete_instance_profile(NAME)