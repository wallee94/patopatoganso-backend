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
    ml_id = models.CharField(max_length=20, null=False, blank=False)
    title = models.CharField(max_length=150, null=False, blank=False)
    clean_title = models.CharField(max_length=150, null=False, blank=False)
    url = models.CharField(max_length=200, null=False, blank=False)
    first_date = models.DateField()
    last_date = models.DateField()
    last_price = models.FloatField(null=False, blank=False)
    is_new = models.BooleanField(default=True)
    free_shipping = models.BooleanField(default=False)
    accepts_mercadopago = models.BooleanField(default=False)
    sold_quantity = models.IntegerField(default=0)
    available_quantity = models.IntegerField(default=1)
    address = models.CharField(max_length=70, null=True, blank=True)

    def __str__(self):
        return self.title


class Price(models.Model):
    report = models.ForeignKey(Report, related_name="from_report")
    price = models.FloatField(null=False, blank=False)
    first_date = models.DateField()

    def __str__(self):
        return self.report.title


class Job(models.Model):
    code = models.CharField(max_length=15, null=False, blank=False)
    date = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.code


class Keyword(models.Model):
    keyword = models.CharField(max_length=50, null=False, blank=False, unique=True)

    def __str__(self):
        return self.keyword
