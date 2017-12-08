from __future__ import absolute_import, unicode_literals

from datetime import datetime, timedelta

import re
from celery import task
from django.db import transaction
from scrapinghub import ScrapinghubClient
from .utils import get_clean_title

from .models import Report, Price, Job


@task()
def task_get_data_from_scrapinghub():
    api_key = "1e2574a9c31941c4afce251ed2102004"
    client = ScrapinghubClient(api_key)
    project = client.get_project(260622)

    # iter through last 8 jobs by newer first
    for job_dict in project.jobs.iter(spider='mercadolibre.com.mx', state='finished', count=8):
        job_key = job_dict.get("key")

        # if the job haven't been saved before, save its items
        if job_key and not Job.objects.filter(code=job_key):
            old_reports = {}
            print("Getting data from job = %s" % job_key)

            # import recent reports from db to cache to avoid multiple commits
            for report in Report.objects.filter(last_date__gte=str(datetime.now().date() - timedelta(7))):
                old_reports[report.ml_id] = report

            items_done = set()
            prices_qs = {}
            reports_qs = []

            scraping_job = project.jobs.get(job_dict["key"])
            for item in scraping_job.items.iter():
                item_id = item.get("id")

                # if item was already saved in this job, escape it
                if item_id in items_done:
                    continue

                date = datetime.strptime(item.get("date"), "%Y-%m-%d").date()
                item_price = float(clean_price(item.get("price")))
                if item_id in old_reports:
                    # if the report already exists, it must be newer than the item due to the jobs iter order
                    # so we just have to update the first_date field
                    report = old_reports[item_id]
                    report.first_date = date
                    reports_qs.append(report)

                    if report.last_price != item_price:
                        # if price changed, save new price instance
                        new_price = Price()
                        new_price.price = item_price
                        new_price.last_date = date
                        prices_qs[report.ml_id] = new_price

                else:
                    # if there's no report yet for this item, create it
                    title = item.get("title")
                    report = Report()
                    report.ml_id = item_id
                    report.title = title
                    report.clean_title = get_clean_title(title)
                    report.url = item.get("url")
                    report.first_date = date
                    report.last_date = date
                    report.last_price = item_price
                    report.is_new = item.get("is_new")
                    reports_qs.append(report)

                    new_price = Price()
                    new_price.price = item_price
                    new_price.last_date = date
                    prices_qs[report.ml_id] = new_price

                items_done.add(item_id)

            # save everything in one commit
            with transaction.atomic():
                for report in reports_qs:
                    report.save()
                    price = prices_qs.get(report.ml_id)
                    if price:
                        price.report = report
                        price.save()

            # update jobs db
            job = Job()
            job.code = job_key
            job.save()
            print("Data saved in db for job = %s" % job_key)


def clean_price(price):
    return re.sub(r'[^\d+\.]', '', price)

