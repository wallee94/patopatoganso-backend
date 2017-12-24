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


def export_reports_to_es():
    es = Elasticsearch("http://45.77.161.88:9200")

    actions = []
    for i, report in enumerate(Report.objects.all()):
        action = {
            "_op_type": "create",
            "_index": "ppg-mml",
            "_type": "report",
            "_id": str(report.id),
            "ml-id": report.ml_id,
            "title": report.title,
            "first_date": report.first_date,
            "last_date": report.last_date,
            "last_price": report.last_price,
            "is_new": report.is_new,
            "free_shipping": report.free_shipping,
            "accepts_mercadopago": report.accepts_mercadopago,
            "sold_quantity": report.sold_quantity,
            "address": report.address
        }
        actions.append(action)

        if i % 2000 == 0:
            print("sending chunk with 2000 elements")
            res = bulk(es, actions)
            print(res)
            actions = []

    bulk(es, actions)
