import logging
import time

from boto.ec2 import EC2Connection


def create_keypair(key_name):
    '''
    Create a new keypair in Amazon and store it locally
    '''
    if not keypair_exists(key_name):
        conn = EC2Connection()
        
        logging.info('Creating keypair: %s' % key_name)
        # Create an SSH key to use when logging into instances.
        key = conn.create_key_pair(key_name)
        
        # AWS will store the public key but the private key is
        # generated and returned and needs to be stored locally.
        key.save('.')
        
        for _ in xrange(20):
            if keypair_exists(key_name):
                break
            
            logging.debug('Waiting for keypair to be available...')
            time.sleep(2)
        else:
            raise RuntimeError('Failed to create keypair %s' % key_name)
        
        return key_name
    else:
        return key_name

        
def keypair_exists(key_name):
    '''
    Check to see if specified keypair already exists.
    If we get an InvalidKeyPair.NotFound error back from EC2,
    it means that it doesn't exist and we need to create it.
    '''
    conn = EC2Connection()
    
    try:
        conn.get_all_key_pairs(keynames=[key_name])[0]
    except conn.ResponseError, e:
        if e.code == 'InvalidKeyPair.NotFound':
            return False
        raise
    
    return True
