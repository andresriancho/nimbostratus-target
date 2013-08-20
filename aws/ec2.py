import time
import logging

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



