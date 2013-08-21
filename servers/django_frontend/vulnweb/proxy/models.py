from django.db import models
from django.utils.timezone import now


class Log(models.Model):
    url = models.CharField(max_length=1024)
    log_date = models.DateTimeField('log date', default=now)