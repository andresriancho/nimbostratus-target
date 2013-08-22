import time
import logging
import socket

import MySQLdb as mdb

from core.region_connection import RDSConnection


DB_NAME = "nimbostratus"
DB_PASSWORD = 'hunter2.'
DB_USER = 'root'

LOW_PRIV_USER = 'noroot'
LOW_PRIV_PASSWORD = 'logs4life'

SG_NAME = 'all_hosts'

SUCCESS_MESSAGE = '''\
Anyone can connect to this MySQL instance at:
    - Host: %s
    - Port: %s
    
    Using root:
        mysql -u %s -p%s -h %s
    
    Using low privileged user:
        mysql -u %s -p%s -h %s
'''


def spawn_rds():
    logging.info('Spawning a new RDS instance, this takes at least 10min!')
    conn = RDSConnection()
    
    db = conn.create_dbinstance(DB_NAME, 5, 'db.m1.small', DB_USER, DB_PASSWORD)
    
    while True:
        try:
            db = conn.get_all_dbinstances(instance_id=DB_NAME)[0]
        except Exception, e:
            logging.debug('Unexpected exception "%s"' % e)
        else:
            if db.endpoint is not None and db.status == 'available':
                break

        time.sleep(45)
        logging.debug('Waiting...')
        
    # Remove if exists, else continue
    try:
        conn.delete_dbsecurity_group(SG_NAME)
    except:
        pass
    
    # Very insecure, everyone can connect to this MySQL instance
    sg = conn.create_dbsecurity_group(SG_NAME, 'All hosts can connect')
    sg.authorize(cidr_ip='0.0.0.0/0')
    db.modify(security_groups=[sg])
    
    logging.info('Successfully started RDS instance.')
    logging.debug(SUCCESS_MESSAGE % (db.endpoint[0], db.endpoint[1],
                                     DB_USER, DB_PASSWORD, db.endpoint[0],
                                     LOW_PRIV_USER, LOW_PRIV_PASSWORD, db.endpoint[0]))
    
    # Wait for the DNS entry to be there...
    time.sleep(5)
    while True:
        try:
            socket.gethostbyname(db.endpoint[0])
            break
        except:
            time.sleep(1)
    
    setup_db(db)
    
    return db

def setup_db(db):
    '''
    Setup the DB:
        * Create a DB for important information
        * Add important sample information
        * Create a DB for logs
        * Create a low privileged user that can only access logs
        
    '''
    logging.info('Loading database information')
    
    host, _ = db.endpoint
    try:
        con = mdb.connect(host, DB_USER, DB_PASSWORD);
    
        # Create the databases
        cur = con.cursor()
        cur.execute('CREATE DATABASE IF NOT EXISTS important')
        cur.execute('CREATE DATABASE IF NOT EXISTS logs')
        con.commit()
        
        # Create low privileged user
        cur.execute("CREATE USER '%s'@'%%' IDENTIFIED BY '%s'" % (LOW_PRIV_USER,
                                                                  LOW_PRIV_PASSWORD))
        sql = "GRANT ALL PRIVILEGES ON logs.* TO '%s'@'%%' WITH GRANT OPTION;"
        cur.execute(sql % LOW_PRIV_USER)
        cur.execute('FLUSH PRIVILEGES')
        con.commit()
        
        # Get a cursor to work on the important DB
        con = mdb.connect(host, DB_USER, DB_PASSWORD, 'important');
        cur = con.cursor()
        sql = '''CREATE TABLE foo (
               bar VARCHAR(50) DEFAULT NULL
               ) ENGINE=MyISAM DEFAULT CHARSET=latin1
               '''
        cur.execute(sql)
        
        sql = "INSERT INTO foo(bar) VALUES (%s)"
        for info in ('42', 'key to the kingdom', 'the meaning of life'):
            cur.execute(sql, (info,))
        con.commit()
        
        logging.info('Done loading database information')
        
    except mdb.Error, e:
        logging.critical("Database error %d: %s" % (e.args[0],e.args[1]))
    finally:    
        if con:    
            con.close()


def teardown_rds():
    logging.warn('Removing RDS instance')
    conn = RDSConnection()
    
    try:
        db_inst = conn.get_all_dbinstances(instance_id=DB_NAME)[0]
    except:
        logging.debug('There was no RDS instance with name %s' % DB_NAME)
        return
    
    conn.delete_dbinstance(db_inst.id, skip_final_snapshot=True)

    while True:
        try:
            conn.get_all_dbinstances(instance_id=DB_NAME)[0]
        except:
            break
        else:
            time.sleep(30)
            logging.debug('Waiting...') 
    
    try:
        conn.delete_dbsecurity_group(SG_NAME)
    except:
        logging.debug('No DB security group %s to delete' % SG_NAME)
    