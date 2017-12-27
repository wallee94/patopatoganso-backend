from datetime import datetime, timedelta

import numpy as np
from elasticsearch import Elasticsearch
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Price, Keyword
from .serializers import KeywordSerializer


class KeywordAPIView(APIView):
    def get(self, request):
        keywords_data = {
            "keywords": Keyword.objects.values_list('keyword', flat=True)
        }
        return Response(data=keywords_data, status=status.HTTP_200_OK)

    def put(self, request):
        if request.user.is_staff:
            keyword_ser = KeywordSerializer(data=request.data)
            if keyword_ser.is_valid():
                keyword_obj = keyword_ser.save()
                return Response(data={"details": "keyword created with id = [%d]" % keyword_obj.id},
                                status=status.HTTP_200_OK)
            return Response(data=keyword_ser.errors, status=status.HTTP_400_BAD_REQUEST)
        return Response(data={"details": "No valid credential provided"}, status=status.HTTP_401_UNAUTHORIZED)


class PriceAPIVIew(APIView):
    permission_classes = (AllowAny, )

    def get(self, request):
        q = request.query_params.get("q")
        is_new = request.query_params.get("new", "true").strip()
        if not q:
            return Response(data={"details": "q query param missing"}, status=status.HTTP_400_BAD_REQUEST)

        q = q.strip()
        today = datetime.now().date()
        date_gte = today - timedelta(30)  # shows last 30 days

        # validations
        if is_new == "true":
            is_new = True
        elif is_new == "false":
            is_new = False
        else:
            return Response(data={"details": "new flag unknown"}, status=status.HTTP_400_BAD_REQUEST)

        size = int(20 + 120/(1 + 2.71828**(len(q.split())-2)))  # sigmoid function

        es = Elasticsearch("http://45.77.161.88:9200")
        body = {
            "size": size,
            "query": {
                "bool": {
                    "must": [
                        {
                            "match": {
                                "title": q
                            }
                        },
                        {
                            "match": {
                                "is_new": is_new
                            }
                        },
                        {
                            "range": {
                                "last_date": {
                                    "gte": date_gte
                                }
                            }
                        }
                    ]
                }
            },
            "_source": ["last_price"]
        }

        hits = es.search(index="ppg-mml", doc_type="report", body=body).get("hits", {"hits": []}).get("hits", [])
        last_prices = list(map(lambda x: x.get("_source", {}).get("last_price"), hits))
        mean = np.mean(last_prices)
        std = np.std(last_prices)
        hits = list(filter(lambda x: mean - std <= x.get("_source", {}).get("last_price") <= mean + std, hits))

        reports = list(map(lambda x: x.get("_id"), hits))

        # order prices by report and then by date
        prices = []
        for price in Price.objects.filter(report__in=reports).select_related("report"):
            prices.append({
                "price": price.price,
                "first_date": price.first_date,
                "report_id": price.report_id,
                "last_date": price.report.last_date
            })

        prices = sorted(prices, key=lambda p: (p["report_id"], p["first_date"]), reverse=True)
        response_data = {}
        for i in range(30):
            date = date_gte + timedelta(i)
            label = str(date)
            response_data[label] = []
            last_report = None
            for price in prices:
                if price["first_date"] <= date <= price["last_date"] and price["report_id"] != last_report:
                    last_report = price["report_id"]
                    response_data[label].append(price["price"])

            if not response_data[label]:
                response_data.pop(label, None)
            else:
                response_data[label] = {
                    "mean": np.mean(response_data[label]),
                    "std": np.std(response_data[label]),
                    "min": np.min(response_data[label]),
                    "max": np.max(response_data[label]),
                    "total": len(response_data[label])
                }
        return Response(data=response_data, status=status.HTTP_200_OK)
