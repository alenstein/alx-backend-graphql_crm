import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'alx_backend_graphql_crm.settings')
django.setup()

from crm.models import Customer, Product

def seed_db():
    Customer.objects.all().delete()
    Product.objects.all().delete()

    Customer.objects.create(name='John Doe', email='john.doe@example.com', phone='123-456-7890')
    Customer.objects.create(name='Jane Smith', email='jane.smith@example.com', phone='+19876543210')

    Product.objects.create(name='Laptop', price=1200.00, stock=10)
    Product.objects.create(name='Mouse', price=25.00, stock=50)
    Product.objects.create(name='Keyboard', price=75.00, stock=30)

    print("Database seeded!")

if __name__ == '__main__':
    seed_db()
