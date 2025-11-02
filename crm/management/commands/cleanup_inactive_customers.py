from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from crm.models import Customer
from django.db.models import Q


class Command(BaseCommand):
    help = 'Delete customers with no orders in the past year or who never placed an order and were created over a year ago'

    def handle(self, *args, **options):
        one_year_ago = timezone.now() - timedelta(days=365)
        
        # Find customers who:
        # 1. Have no orders at all and were created over a year ago, OR
        # 2. Have orders but all orders are older than a year
        inactive_customers = Customer.objects.filter(
            Q(orders__isnull=True, created_at__lt=one_year_ago) |
            Q(orders__order_date__lt=one_year_ago)
        ).exclude(
            orders__order_date__gte=one_year_ago
        ).distinct()
        
        deleted_count = inactive_customers.count()
        inactive_customers.delete()
        
        self.stdout.write(
            self.style.SUCCESS(f'{deleted_count} inactive customer(s) deleted.')
        )
        
        return deleted_count
