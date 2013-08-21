BROKER_TRANSPORT = 'sqs'
BOTO_PROVIDER = 'boto-provider'
BROKER_URL = '%s://%s:%s@' % (BROKER_TRANSPORT, BOTO_PROVIDER, None)
CELERY_IGNORE_RESULT = True
BROKER_TRANSPORT_OPTIONS = {
                            'queue_name_prefix': 'nimbostratus-',
                            'region': 'ap-southeast-1',
}