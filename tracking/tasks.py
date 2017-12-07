from __future__ import absolute_import, unicode_literals

from datetime import datetime
from time import time

import re
from celery import task
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
            start_time = time()
            print("Starting job = %s" % job_key)

            scraping_job = project.jobs.get(job_dict["key"])
            items = {}

            for item in scraping_job.items.iter():
                items[item.get("id")] = item
            items_ids = list(items.keys())
            prices_qs = {}
            reports_qs = []

            old_reports = Report.objects.filter(ml_id__in=items_ids)
            for report in old_reports:
                item = items.get(report.ml_id)
                date = datetime.strptime(item.get("date"), "%Y-%m-%d").date()
                item_price = float(clean_price(item.get("price")))

                if report.last_date > date:
                    report.last_date = date
                    report.last_price = item_price
                reports_qs.append(report)

                if report.last_price != item_price:
                    # if price changed, save new price instance
                    new_price = Price()
                    new_price.price = item_price
                    new_price.date = date
                    prices_qs[report.ml_id] = new_price

                items_ids.remove(report.ml_id)

            for item_id in items_ids:
                # if report does not exist, save new report and price instances
                item = items.get(item_id)
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
                new_price.date = date
                prices_qs[report.ml_id] = new_price

            print("Atomic transaction started after %f sec" % (time() - start_time))
            # save everything in one commit
            with transaction.atomic():
                for report in reports_qs:
                    report.save()
                    price = prices_qs.get(report.ml_id)
                    if price:
                        price.report = report
                        price.save()

            job = Job()
            job.code = job_key
            job.save()
            print("Job done in %f sec" % (time() - start_time))

def clean_price(price):
    return re.sub(r'[^\d+]', '', price)