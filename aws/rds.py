from core.region_connection import RDSConnection, EC2Connection
from servers.celery_backend.deploy import SG_NAME


def spawn_rds():
    conn = RDSConnection()
    
    db = conn.create_dbinstance("db-master-1", 10, 'db.m1.small', 'root', 'hunter2')
    
    # Allow access from the celery worker security group
    ec2_conn = EC2Connection()
    sg = ec2_conn.get_all_security_groups(groupnames=[SG_NAME,])[0]
    db.modify(security_groups=[sg])

def teardown_rds():
    conn = RDSConnection()
