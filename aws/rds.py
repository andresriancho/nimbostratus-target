import time
import logging

from core.region_connection import RDSConnection, EC2Connection
from servers.celery_backend.deploy import SG_NAME


DB_NAME = "nimbostratus"
SUCCESS_MESSAGE = '''\
Allowed instances will be able to connect via:
    - Host: %s
    - Port: %s
'''


def spawn_rds():
    logging.info('Spawning a new RDS instance, this takes at least 10min!')
    conn = RDSConnection()
    
    db = conn.create_dbinstance(DB_NAME, 1, 'db.m1.small', 'root', 'hunter2')
    
    # Allow access from the celery worker security group
    ec2_conn = EC2Connection()
    sg = ec2_conn.get_all_security_groups(groupnames=[SG_NAME,])[0]
    db.modify(security_groups=[sg])
    
    logging.info('Successfully started RDS instance.')
    logging.debug(SUCCESS_MESSAGE % db.endpoint)

def teardown_rds():
    logging.warn('Removing RDS instance')
    conn = RDSConnection()
    
    db_inst = conn.get_all_dbinstances(instance_id=DB_NAME)[0]
    conn.delete_dbinstance(db_inst.id, skip_final_snapshot=True)

    while True:
        try:
            conn.get_all_dbinstances(instance_id=DB_NAME)[0]
        except:
            break
        else:
            time.sleep(30)
            logging.debug('Waiting...') 