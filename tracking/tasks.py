from __future__ import absolute_import, unicode_literals

from datetime import datetime

import re
from celery import task
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
            for item in scraping_job.items.iter():
                date = datetime.strptime("2017-12-12", item.get("date"))
                prices = Price.objects.filter(report__id=item.get("id")).order_by("-date")
                item_price = float(clean_price(item.get("price")))

                if prices:
                    # if prices is not empty, update the last_date from the report
                    report = prices.first().report
                    report.last_date = max(date, report.last_date)

                    if prices.first().price != item_price:
                        # if price changed, save new price instance
                        new_price = Price()
                        new_price.price = item_price
                        new_price.report = prices.first().report
                        new_price.save()

                else:
                    # if price QuerySet is empty, save new report and price instances
                    report = Report()
                    report.ml_id = item.get("id")
                    report.title = item.get("title")
                    report.url = item.get("url")
                    report.last_date = date
                    report.is_new = item.get("is_new")
                    report.save()

                    new_price = Price()
                    new_price.price = item_price
                    new_price.report = report
                    new_price.save()


def clean_price(price):
    return re.sub(r'[^\d+]', '', price)