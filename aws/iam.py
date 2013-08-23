import logging
from core.region_connection import IAMConnection

IAM_USER = 'low_privileged_user'
IAM_GROUP = 'low_privileged_group'
GROUP_PRIVILEGES = '''\
{
  "Statement": [
    {
      "Sid": "Stmt1377108934836",
      "Action": "iam:*",
      "Effect": "Allow",
      "Resource": "*"
    },
    {
      "Sid": "Stmt1377109045369",
      "Action": "sqs:*",
      "Effect": "Allow",
      "Resource": "*"
    }
  ]
}
'''



def spawn_iam_user():
    '''
    Create an IAM user and return the API key and secret.
    '''
    teardown_iam_user()
    
    conn = IAMConnection()
    conn.create_user(IAM_USER)
    credentials = conn.create_access_key(user_name=IAM_USER)
    
    key = credentials['create_access_key_response']['create_access_key_result']['access_key']
    api_key = key['access_key_id']
    api_secret = key['secret_access_key']

    conn.create_group(IAM_GROUP)
    conn.add_user_to_group(IAM_GROUP, IAM_USER)

    conn.put_group_policy(IAM_GROUP, 'LowPrivsPolicy', GROUP_PRIVILEGES)
    
    return api_key, api_secret

def teardown_iam_user():
    '''
    Remove the IAM user
    '''
    conn = IAMConnection()
    try:
        conn.remove_user_from_group(IAM_GROUP, IAM_USER)
        
        access_keys_response = conn.get_all_access_keys(IAM_USER)
        access_keys = access_keys_response['list_access_keys_response']['list_access_keys_result']['access_key_metadata']
        
        for access_key in access_keys:
            conn.delete_access_key(access_key['access_key_id'], user_name=IAM_USER)
            
        conn.delete_user(IAM_USER)
        conn.delete_group_policy(IAM_GROUP, 'LowPrivsPolicy')
        conn.delete_group(IAM_GROUP)
    except:
        logging.debug('IAM user component missing. Not removed.')