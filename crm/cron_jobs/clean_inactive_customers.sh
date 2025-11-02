#!/bin/bash
# This script deletes customers with no orders in the last year.

# Navigate to the project directory
cd /home/alensteinx/Software_Engineer/_alx_sandbox/alx-backend-graphql_crm || exit


# Run the Django management command to delete inactive customers
output=$(python manage.py shell <<EOF
from datetime import timedelta
from django.utils import timezone
from crm.models import Customer

one_year_ago = timezone.now() - timedelta(days=365)
inactive_customers = Customer.objects.filter(order__date_ordered__lt=one_year_ago)
deleted_count, _ = inactive_customers.delete()
print(f"{deleted_count} inactive customers deleted.")
EOF
)

# Log the output
echo "$(date): $output" >> /tmp/customer_cleanup_log.txt
