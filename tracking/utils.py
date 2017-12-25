import re
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

from .models import Report


def get_clean_title(title):
    clean_title = title.lower()
    clean_title = re.sub(r'á', 'a', clean_title)
    clean_title = re.sub(r'é', 'e', clean_title)
    clean_title = re.sub(r'í', 'i', clean_title)
    clean_title = re.sub(r'ó', 'o', clean_title)
    clean_title = re.sub(r'ú', 'u', clean_title)
    clean_title = re.sub(r'ü', 'u', clean_title)
    clean_title = re.sub(r'[^\w\d\s]', '', clean_title)

    return clean_title.strip()


# CAUTION: don't use this method in server. It requires a lot of RAM.
#  as a rule of thumb, 1,000,000 reports need 1.11 GB aprox
def export_reports_to_es():
    es = Elasticsearch("http://45.77.161.88:9200")

    actions = []
    for i, report in enumerate(Report.objects.all().values("id", "ml_id", "title", "first_date", "last_date",
                                                           "is_new", "free_shipping", "accepts_mercadopago",
                                                           "sold_quantity", "address", "last_price")):
        action = {
            "_op_type": "create",
            "_index": "ppg-mml",
            "_type": "report",
            "_id": str(report["id"]),
            "ml-id": report["ml_id"],
            "title": report["title"],
            "first_date": report["first_date"],
            "last_date": report["last_date"],
            "is_new": report["is_new"],
            "free_shipping": report["free_shipping"],
            "last_price": report["last_price"],
            "accepts_mercadopago": report["accepts_mercadopago"],
            "sold_quantity": report["sold_quantity"],
            "address": report["address"]
        }
        actions.append(action)

        # save data un bulk with 2000 items each
        if i % 2000 == 0:
            bulk(es, actions)
            actions = []

    bulk(es, actions)
