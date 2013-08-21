from __future__ import print_function

import time
import sys
import socket
import logging


def wait_ssh_ready(host, tries=40, delay=3, port=22):
    # Wait until the SSH is actually up
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    logging.info('Waiting for SSH at %s to be ready to connect' % host, end='')
    sys.stdout.flush()
    
    for _ in xrange(tries):
        try:
            s.connect((host, port))
            assert s.recv(3) == 'SSH'
        except KeyboardInterrupt:
            logging.warn('User stopped the loop.')
            break
        except socket.error:
            time.sleep(delay)
            print('.', end='')
            sys.stdout.flush()
        except AssertionError:
            time.sleep(delay)
            print('!', end='')
            sys.stdout.flush()
        else:
            print() # A new line
            logging.info('SSH is ready to connect')
            return True
    else:
        waited = tries * delay
        logging.error('SSH is not available after %s seconds.' % waited)
        return False