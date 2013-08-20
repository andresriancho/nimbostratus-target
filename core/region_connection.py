import boto.ec2

from config import REGION


def EC2Connection():
    return boto.ec2.connect_to_region(REGION)