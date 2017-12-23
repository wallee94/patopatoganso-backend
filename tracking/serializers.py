from rest_framework import serializers

from .models import Price, Keyword


class PriceResponseSerializer(serializers.ModelSerializer):

    class Meta:
        model = Price
        fields = '__all__'


class KeywordSerializer(serializers.ModelSerializer):

    class Meta:
        model = Keyword
        fields = '__all__'