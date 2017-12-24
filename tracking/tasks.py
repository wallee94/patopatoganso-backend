from __future__ import absolute_import, unicode_literals

import smtplib
from datetime import datetime, timedelta
from email.mime.text import MIMEText

from celery import task
from django.conf import settings
from django.db import transaction
from scrapinghub import ScrapinghubClient

from .models import Report, Price, Job
from .utils import get_clean_title


@task()
def task_get_data_from_scrapinghub():
    api_key = "1e2574a9c31941c4afce251ed2102004"
    client = ScrapinghubClient(api_key)
    project = client.get_project(260622)

    # iter through last 8 jobs by older first
    jobs_list = project.jobs.list(spider='api-mercadolibre.com.mx', state='finished', count=10)[::-1]
    for job_dict in jobs_list:
        job_key = job_dict.get("key")

        # if the job haven't been saved before, save its items
        if job_key and not Job.objects.filter(code=job_key):
            old_reports = {}
            print("Getting data from job = %s" % job_key)

            # import recent reports from db to cache to avoid multiple commits
            for id, ml_id, last_price in Report.objects.filter(last_date__gte=str(datetime.now().date() - timedelta(7))).values_list('id', 'ml_id', 'last_price'):
                old_reports[ml_id] = {"id": id, "last_price": last_price}

            items_done = set()
            scraping_job = project.jobs.get(job_dict["key"])

            # save everything in one commit
            with transaction.atomic():
                for item in scraping_job.items.iter():
                    item_id = item.get("id")

                    # if item was already saved in this job, escape it
                    if item_id in items_done:
                        continue

                    item_date = datetime.strptime(item.get("date"), "%Y-%m-%d").date()
                    item_price = item.get("price")
                    if item_id in old_reports:
                        # if the report already exists, the new item must be more recent
                        report = old_reports[item_id]
                        if report.get("last_price") != item_price:
                            # if price changed, save new price instance
                            new_price = Price(report_id=report.get("id"), price=item_price, first_date=item_date)
                            new_price.save()

                            Report.objects.filter(pk=report.get("id")).update(last_date=item_date, last_price=item_price)

                        else:
                            Report.objects.filter(pk=report.get("id")).update(last_date=item_date)

                    else:
                        title = item["title"][:150]
                        url = item["url"]
                        if len(url) > 200:
                            url_id = item.get("site_id", "MLM") + "-" + item_id.split(item.get("site_id", "MLM"))[-1]
                            url = "https://articulo.mercadolibre.com.mx/" + url_id + "-product-_JM"
                        new_report = Report(
                            ml_id=item_id,
                            title=title,
                            clean_title=get_clean_title(title),
                            url=url,
                            first_date=item_date,
                            last_date=item_date,
                            last_price=item_price,
                            is_new=item.get("is_new"),
                            free_shipping=item.get("free_shipping"),
                            accepts_mercadopago=item.get("accepts_mercadopago"),
                            sold_quantity=item.get("sold_quantity"),
                            available_quantity=item.get("available_quantity"),
                            address=item.get("address")
                        )
                        new_report.save()

                        new_price = Price(report=new_report, price=item_price, first_date=item_date)
                        new_price.save()

                    items_done.add(item_id)

            # update jobs db
            job = Job()
            job.code = job_key
            job.save()
            print("Data saved in db for job = %s" % job_key)

    send_email_report()


def send_email_report():
    server = smtplib.SMTP(settings.REPORT_EMAIL_SERVER)
    server.ehlo()
    server.starttls()
    server.login(settings.REPORT_EMAIL_USER, settings.REPORT_EMAIL_PASSWORD)

    for member in settings.LIST_EMAIL_MEMBERS:
        msg = MIMEText("Los productos de mercadolibre.com.mx fueron exitosamente guardados en la base de datos")
        msg['Subject'] = "mercadolibre.com.mx - " + str(datetime.now().date())
        msg['From'] = settings.REPORT_EMAIL_USER
        msg['To'] = member
        server.send_message(msg)
