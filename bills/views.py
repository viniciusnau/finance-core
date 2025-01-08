from datetime import datetime

from django.db import DatabaseError
from django.db.models import Sum, Q, Value, Case, When, DateField, F
from rest_framework import generics, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Debt, Category
from .serializers import DebtSerializer, CategorySerializer, CreateDebtSerializer
from rest_framework.permissions import IsAuthenticated, IsAdminUser


class DebtListView(generics.ListCreateAPIView):
    queryset = Debt.objects.all()
    serializer_class = DebtSerializer
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return CreateDebtSerializer
        return DebtSerializer

    def get_queryset(self):
        queryset = Debt.objects.filter(user=self.request.user)
        start_date = self.request.query_params.get('start_date', None)
        end_date = self.request.query_params.get('end_date', None)
        search = self.request.query_params.get('search', None)
        debt_status = self.request.query_params.get('status', None)

        if start_date:
            try:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
                queryset = queryset.filter(due_date__gte=start_date)
            except ValueError:
                raise ValidationError("Invalid start_date format. Please use YYYY-MM-DD.")

        if end_date:
            try:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
                queryset = queryset.filter(due_date__lte=end_date)
            except ValueError:
                raise ValidationError("Invalid end_date format. Please use YYYY-MM-DD.")

        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(notes__icontains=search)
            )

        if debt_status:
            valid_statuses = [Debt.PENDING, Debt.OVERDUE, Debt.PAID]
            if debt_status not in valid_statuses:
                raise ValidationError("Invalid status value. Valid options are: PENDING, OVERDUE, PAID.")
            queryset = queryset.filter(status=debt_status)

        distant_future = datetime(9999, 12, 31).date()

        queryset = queryset.annotate(
            overdue_priority=Case(
                When(status=Debt.OVERDUE, then=F('due_date')),
                default=Value(distant_future, output_field=DateField()),
                output_field=DateField()
            ),
            upcoming_priority=Case(
                When(status=Debt.PENDING, then=F('due_date')),
                default=Value(distant_future, output_field=DateField()),
                output_field=DateField()
            )
        ).order_by(
            'overdue_priority',
            'upcoming_priority',
            'status'
        )

        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DebtDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Debt.objects.all()
    serializer_class = DebtSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Debt.objects.filter(user=self.request.user)


class CategoryListView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminUser]


class MeApi(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            debts = Debt.objects.filter(user=request.user)

            total_debts = debts.count()
            total_debts_amount_sum = debts.aggregate(Sum('amount'))['amount__sum'] or 0
            total_paid_debts_sum = debts.filter(status=Debt.PAID).aggregate(Sum('amount'))['amount__sum'] or 0
            total_overdue_debts_sum = debts.filter(status=Debt.OVERDUE).aggregate(Sum('amount'))['amount__sum'] or 0
            total_pending_debts_sum = debts.filter(status=Debt.PENDING).aggregate(Sum('amount'))['amount__sum'] or 0

            total_paid_debts = debts.filter(status=Debt.PAID).count()
            total_overdue_debts = debts.filter(status=Debt.OVERDUE).count()
            total_pending_debts = debts.filter(status=Debt.PENDING).count()

            financial_summary = {
                'total_debts': total_debts,
                'total_debts_amount_sum': total_debts_amount_sum,
                'total_paid_debts': total_paid_debts,
                'total_paid_debts_sum': total_paid_debts_sum,
                'total_overdue_debts': total_overdue_debts,
                'total_overdue_debts_sum': total_overdue_debts_sum,
                'total_pending_debts': total_pending_debts,
                'total_pending_debts_sum': total_pending_debts_sum,
            }

            return Response(financial_summary)

        except DatabaseError:
            return Response({'detail': 'internal server error.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)
