from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['name'], name='unique_category')
        ]


class Debt(models.Model):
    PENDING = 'Pendente'
    PAID = 'Pago'
    OVERDUE = 'Atrasado'

    STATUS_CHOICES = [
        (PENDING, 'Pendente'),
        (PAID, 'Pago'),
        (OVERDUE, 'Atrasado'),
    ]

    title = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=PENDING
    )
    notes = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="debts")
    email_sent_for_due_soon = models.BooleanField(default=False)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=False, blank=False, default=9, related_name="debts")

    def __str__(self):
        return f"{self.title} - {self.amount} ({self.status})"
