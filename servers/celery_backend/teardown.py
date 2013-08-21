import logging

from core.region_connection import EC2Connection

from aws.ec2 import terminate_instance, get_instances_to_terminate
from servers.celery_backend.deploy import NAME, SG_NAME


def teardown_celery_backend():
    for inst in get_instances_to_terminate(NAME):
        terminate_instance(inst)

    logging.debug('Removing keypair "%s"' % NAME)        
    conn = EC2Connection()
    conn.delete_key_pair(NAME)

    try:
        conn.get_all_security_groups(groupnames=[SG_NAME,])
    except:
        logging.debug('No security group "%s" to delete' % NAME)
    else:
        logging.debug('Removing security group "%s"' % NAME)
        conn.delete_security_group(SG_NAME)
