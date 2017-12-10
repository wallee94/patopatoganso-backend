from datetime import datetime, timedelta

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Price, Report
from .serializers import PriceResponseSerializer
from .utils import get_clean_title


class PriceAPIVIew(APIView):
    def get(self, request):
        q = request.query_params.get("q")
        if not q:
            return Response(data={"details": "q query param missing"}, status=status.HTTP_400_BAD_REQUEST)

        date_gte = datetime.now().date() - timedelta(30)  # shows last 30 days
        clean_title = get_clean_title(q)
        words = clean_title.split()[:8]  # 8 words is the limit
        reports = Report.objects.filter(last_date__gte=date_gte)
        for word in words:
            reports = reports.filter(clean_title__contains=word.strip())
        prices = Price.objects.filter(report__in=reports)

        return Response(data=PriceResponseSerializer(prices, many=True).data, status=status.HTTP_200_OK)
