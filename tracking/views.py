from datetime import datetime, timedelta

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
import numpy as np

from .models import Price, Report
from .utils import get_clean_title


class PriceAPIVIew(APIView):
    permission_classes = (AllowAny, )

    def get(self, request):
        q = request.query_params.get("q")
        fit = request.query_params.get("fit", "term").strip()
        is_new = request.query_params.get("new", "true").strip()
        if not q:
            return Response(data={"details": "q query param missing"}, status=status.HTTP_400_BAD_REQUEST)

        q = q.strip()
        today = datetime.now().date()
        date_gte = today - timedelta(30)  # shows last 30 days
        clean_title = get_clean_title(q)

        # validations
        if is_new == "true":
            is_new = True
        elif is_new == "false":
            is_new = False
        else:
            return Response(data={"details": "new flag unknown"}, status=status.HTTP_400_BAD_REQUEST)

        reports = Report.objects.filter(last_date__gte=date_gte, is_new=is_new)
        if fit == "term":
            words = clean_title.split()[:10]  # 10 words is the limit
            for word in words:
                reports = reports.filter(clean_title__contains=word.strip())
        elif fit == "exact":
            reports = Report.objects.filter(clean_title__contains=q)
        else:
            return Response(data={"details": "fit method unknown"}, status=status.HTTP_400_BAD_REQUEST)

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
                    "max": np.max(response_data[label])
                }
        return Response(data=response_data, status=status.HTTP_200_OK)
