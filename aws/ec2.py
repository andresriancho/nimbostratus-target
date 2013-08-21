import time
import logging

import boto

from core.region_connection import EC2Connection


def terminate_instance(inst):
    '''
    Terminates an instance by name
    
    :param inst: A boto instance object
    :return: None, an exception is raised if something goes wrong
    '''
    conn = EC2Connection()
    
    # Terminate the instance
    logging.critical('Terminating %s instance' % inst.id)
    
    conn.terminate_instances(instance_ids=[inst.id,])
    
    while inst.state != u'terminated':
        logging.debug("%s instance state: %s" % (inst.id, inst.state))
        time.sleep(10)
        inst.update()
        
def get_instances_to_terminate(name):
    '''
    :return: A list with the instance objects which need to be terminated,
             based on the name passed as parameter.
    '''
    to_terminate = []
    
    conn = EC2Connection()

    for reservation in conn.get_all_instances():
        for inst in reservation.instances:
            
            if inst.tags.get('Name', None) == name and\
            inst.state != u'terminated':
                logging.debug('%s is a %s instance' % (inst.id, name))
                
                to_terminate.append(inst)
    
    return to_terminate



def create_instance_profile(name, policy):
    # Remove it before starting
    delete_instance_profile(name)
    
    # Next, you need to create an Instance Profile in IAM.
    c = boto.connect_iam()
    instance_profile = c.create_instance_profile(name)

    # Once you have the instance profile, you need to create the role, 
    # add the role to the instance profile and associate the policy with the role.
    role = c.create_role(name)
    c.add_role_to_instance_profile(name, name)
    c.put_role_policy(name, name, policy)

    # Wait for it to be available
    for _ in xrange(10):
        
        # We want to wait in all cases, because I've seen the roles created
        # and available via the API but not to EC2 instances. So we better wait
        # for at least 1min
        logging.debug('Waiting for role %s to be available...' % name)
        time.sleep(60)
        
        try:
            c.get_role(name)
            c.get_instance_profile(name)
            break
        except:
            pass

    else:
        raise RuntimeError('Role creation for instance profile failed.')

    # Now, you can use that instance profile when you launch an instance
    return name

def delete_instance_profile(name):
    iam = boto.connect_iam()
    
    logging.warn('Removing IAM instance profile "%s"' % name)
    
    try:
        iam.remove_role_from_instance_profile(name, name)
    except Exception, e:
        pass
        
    try:
        iam.get_instance_profile(name)
        iam.delete_instance_profile(name)
    except Exception, e:
        pass
        
    try:
        iam.get_role_policy(name, name)
        iam.delete_role_policy(name, name)
    except Exception, e:
        pass

    try:
        iam.get_role(name)
        iam.delete_role(name)
    except Exception, e:
        pass