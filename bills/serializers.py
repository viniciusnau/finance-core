from rest_framework import serializers
from .models import Category, Debt


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class DebtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Debt
        fields = '__all__'


class CreateDebtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Debt
        fields = ['title', 'amount', 'due_date', 'status', 'notes', 'category']

    notes = serializers.CharField(required=False, allow_blank=True, default=None)
