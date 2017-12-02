from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework.authtoken.models import Token


@receiver(post_save, sender=User)
def create_auth_token(sender, instance=None, created=False, **kwargs):
    if created:
        Token.objects.create(user=instance)


class Report(models.Model):
    title = models.CharField(max_length=150, null=False, blank=False)
    price = models.FloatField()
    date = models.DateField(auto_now_add=True)
    is_new = models.BooleanField()

    def __str__(self):
        return self.title


class Publication(models.Model):
    report = models.ForeignKey(Report, related_name="publication_report")
    url = models.CharField(max_length=300, null=False, blank=False)

    def __str__(self):
        return self.report.title


