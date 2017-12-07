from __future__ import absolute_import, unicode_literals

from datetime import datetime

import re
from celery import task
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from scrapinghub import ScrapinghubClient

from .models import Report, Price, Job


@task()
def task_get_data_from_scrapinghub():
    api_key = "1e2574a9c31941c4afce251ed2102004"
    client = ScrapinghubClient(api_key)
    project = client.get_project(260622)

    for job_dict in project.jobs.iter(spider='mercadolibre.com.mx', state='finished', count=10):
        job_key = job_dict.get("key")

        # if the job haven't been saved before, save its items
        if job_key and not Job.objects.filter(code=job_key):
            job = Job()
            job.code = job_key
            job.save()

            scraping_job = project.jobs.get(job_dict["key"])
            reports_qs = []
            prices_qs = []

            for item in scraping_job.items.iter():
                date = datetime.strptime(item.get("date"), "%Y-%m-%d").date()
                item_price = float(clean_price(item.get("price")))
                try:
                    # if report exists, update it
                    report = Report.objects.get(ml_id=item.get("id"))

                    if report.last_date > date:
                        report.last_date = date
                        report.last_price = item_price
                    reports_qs.append(report)

                    if report.last_price != item_price:
                        # if price changed, save new price instance
                        new_price = Price()
                        new_price.price = item_price
                        new_price.date = date
                        new_price.report = report
                        prices_qs.append(new_price)

                except ObjectDoesNotExist:
                    # if report does not exist, save new report and price instances
                    report = Report()
                    report.ml_id = item.get("id")
                    report.title = item.get("title")
                    report.url = item.get("url")
                    report.last_date = date
                    report.last_price = item_price
                    report.is_new = item.get("is_new")
                    reports_qs.append(report)

                    new_price = Price()
                    new_price.price = item_price
                    new_price.report = report
                    new_price.date = date
                    prices_qs.append(new_price)

            # save everything in one commit
            with transaction.atomic():
                for price in prices_qs:
                    price.save()
                for report in reports_qs:
                    report.save()


def clean_price(price):
    return re.sub(r'[^\d+]', '', price)