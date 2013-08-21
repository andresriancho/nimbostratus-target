import boto.rds
import boto.iam
import boto.ec2

from config import REGION


def EC2Connection():
    return boto.ec2.connect_to_region(REGION)

def RDSConnection():
    return boto.rds.connect_to_region(REGION)

def IAMConnection():
    return boto.iam.connect_to_region('universal')