import os

from celery import shared_task
from django.utils import timezone
from django.core.mail import EmailMultiAlternatives
from datetime import timedelta

from bills.models import Debt


@shared_task
def check_pending_debts():
    today = timezone.now().date()
    tomorrow = today + timedelta(days=1)

    overdue_debts = Debt.objects.filter(status=Debt.PENDING, due_date__lt=today)
    overdue_debts.update(status=Debt.OVERDUE)

    for debt in overdue_debts:
        subject = f"Débito atrasado!"
        from_email = os.environ.get("EMAIL_HOST_USER")
        recipient_list = [debt.user.email]

        email = EmailMultiAlternatives(
            subject=subject,
            body=f"Seu débito: {debt.__str__()} está atrasado!",
            from_email=from_email,
            to=recipient_list,
            reply_to=[from_email],
        )
        email.send()

    almost_due_debts = Debt.objects.filter(status=Debt.PENDING, due_date=tomorrow)

    for debt in almost_due_debts:
        if not debt.email_sent_for_due_soon:
            subject = f"Débito quase atrasado!"
            from_email = os.environ.get("EMAIL_HOST_USER")
            recipient_list = [debt.user.email]

            email = EmailMultiAlternatives(
                subject=subject,
                body=f"Seu débito: {debt.__str__()} está para atrasar amanhã!",
                from_email=from_email,
                to=recipient_list,
                reply_to=[from_email],
            )
            email.send()
            debt.email_sent_for_due_soon = True
            debt.save()

    return f"{overdue_debts.count()} debts marked as overdue and {almost_due_debts.count()} users notified."
