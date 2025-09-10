from django.db import models

class Run(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    path = models.CharField(max_length=512)
