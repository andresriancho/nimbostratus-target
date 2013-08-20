from aws.ec2 import terminate_instance, get_instances_to_terminate
from servers.django_frontend.deploy import NAME


def teardown_django_frontend():
    for inst in get_instances_to_terminate(NAME):
        terminate_instance(inst)
