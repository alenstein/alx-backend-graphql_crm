from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from django.core.management import call_command
from io import StringIO
from crm.models import Customer, Order, Product


class CustomerCleanupTestCase(TestCase):
    """Test cases for customer cleanup logic"""

    def setUp(self):
        """Set up test data"""
        # Create products for orders
        self.product1 = Product.objects.create(name="Product 1", price=10.00, stock=100)
        self.product2 = Product.objects.create(name="Product 2", price=20.00, stock=50)

    def test_delete_customers_with_no_recent_orders(self):
        """
        Test case 1: The customer cleanup logic correctly identifies and deletes 
        customers with no orders in the past year.
        """
        # Create a customer with an old order (over 1 year ago)
        customer = Customer.objects.create(
            name="Old Customer",
            email="old@example.com",
            phone="1234567890"
        )
        # Manually set created_at to over a year ago
        customer.created_at = timezone.now() - timedelta(days=400)
        customer.save()
        
        # Create an order from over a year ago
        old_order = Order.objects.create(
            customer=customer,
            total_amount=10.00
        )
        old_order.order_date = timezone.now() - timedelta(days=400)
        old_order.save()
        old_order.products.add(self.product1)
        
        # Run the cleanup command
        out = StringIO()
        call_command('cleanup_inactive_customers', stdout=out)
        
        # Verify the customer was deleted
        self.assertFalse(Customer.objects.filter(email="old@example.com").exists())
        self.assertIn('1 inactive customer(s) deleted', out.getvalue())

    def test_keep_customers_with_recent_orders(self):
        """
        Test case 2: The customer cleanup logic does not delete customers who 
        have placed an order within the past year.
        """
        # Create a customer with a recent order (within the past year)
        customer = Customer.objects.create(
            name="Active Customer",
            email="active@example.com",
            phone="1234567890"
        )
        
        # Create a recent order (6 months ago)
        recent_order = Order.objects.create(
            customer=customer,
            total_amount=20.00
        )
        recent_order.order_date = timezone.now() - timedelta(days=180)
        recent_order.save()
        recent_order.products.add(self.product1)
        
        # Run the cleanup command
        out = StringIO()
        call_command('cleanup_inactive_customers', stdout=out)
        
        # Verify the customer was NOT deleted
        self.assertTrue(Customer.objects.filter(email="active@example.com").exists())
        self.assertIn('0 inactive customer(s) deleted', out.getvalue())

    def test_no_customers_meet_inactive_criteria(self):
        """
        Test case 3: The customer cleanup logic correctly handles scenarios 
        where no customers meet the inactive criteria.
        """
        # Create multiple customers with recent orders
        for i in range(3):
            customer = Customer.objects.create(
                name=f"Customer {i}",
                email=f"customer{i}@example.com",
                phone=f"123456789{i}"
            )
            order = Order.objects.create(
                customer=customer,
                total_amount=15.00
            )
            order.order_date = timezone.now() - timedelta(days=100)
            order.save()
            order.products.add(self.product2)
        
        # Run the cleanup command
        out = StringIO()
        initial_count = Customer.objects.count()
        call_command('cleanup_inactive_customers', stdout=out)
        
        # Verify no customers were deleted
        self.assertEqual(Customer.objects.count(), initial_count)
        self.assertIn('0 inactive customer(s) deleted', out.getvalue())

    def test_all_customers_meet_inactive_criteria(self):
        """
        Test case 4: The customer cleanup logic correctly handles scenarios 
        where all customers meet the inactive criteria.
        """
        # Create multiple customers with old orders
        customer_emails = []
        for i in range(3):
            customer = Customer.objects.create(
                name=f"Inactive Customer {i}",
                email=f"inactive{i}@example.com",
                phone=f"987654321{i}"
            )
            customer.created_at = timezone.now() - timedelta(days=500)
            customer.save()
            customer_emails.append(customer.email)
            
            order = Order.objects.create(
                customer=customer,
                total_amount=25.00
            )
            order.order_date = timezone.now() - timedelta(days=400)
            order.save()
            order.products.add(self.product1)
        
        # Run the cleanup command
        out = StringIO()
        call_command('cleanup_inactive_customers', stdout=out)
        
        # Verify all customers were deleted
        for email in customer_emails:
            self.assertFalse(Customer.objects.filter(email=email).exists())
        self.assertIn('3 inactive customer(s) deleted', out.getvalue())

    def test_delete_customers_never_ordered_created_over_year_ago(self):
        """
        Test case 5: The customer cleanup logic accurately deletes customers 
        who have never placed an order, if they were created over a year ago.
        """
        # Create a customer with no orders, created over a year ago
        customer = Customer.objects.create(
            name="No Orders Customer",
            email="noorders@example.com",
            phone="5555555555"
        )
        customer.created_at = timezone.now() - timedelta(days=400)
        customer.save()
        
        # Create another customer with no orders, but created recently
        recent_customer = Customer.objects.create(
            name="Recent No Orders",
            email="recentnoorders@example.com",
            phone="6666666666"
        )
        
        # Run the cleanup command
        out = StringIO()
        call_command('cleanup_inactive_customers', stdout=out)
        
        # Verify old customer with no orders was deleted
        self.assertFalse(Customer.objects.filter(email="noorders@example.com").exists())
        
        # Verify recent customer with no orders was NOT deleted
        self.assertTrue(Customer.objects.filter(email="recentnoorders@example.com").exists())
        
        self.assertIn('1 inactive customer(s) deleted', out.getvalue())

    def test_mixed_scenario(self):
        """
        Additional test: Mixed scenario with various customer types to ensure 
        the cleanup logic works correctly in complex situations.
        """
        # Customer 1: Recent order - should NOT be deleted
        c1 = Customer.objects.create(name="C1", email="c1@example.com")
        o1 = Order.objects.create(customer=c1, total_amount=10.00)
        o1.order_date = timezone.now() - timedelta(days=30)
        o1.save()
        o1.products.add(self.product1)
        
        # Customer 2: Old order - should be deleted
        c2 = Customer.objects.create(name="C2", email="c2@example.com")
        c2.created_at = timezone.now() - timedelta(days=500)
        c2.save()
        o2 = Order.objects.create(customer=c2, total_amount=20.00)
        o2.order_date = timezone.now() - timedelta(days=400)
        o2.save()
        o2.products.add(self.product2)
        
        # Customer 3: No orders, old - should be deleted
        c3 = Customer.objects.create(name="C3", email="c3@example.com")
        c3.created_at = timezone.now() - timedelta(days=450)
        c3.save()
        
        # Customer 4: No orders, recent - should NOT be deleted
        c4 = Customer.objects.create(name="C4", email="c4@example.com")
        
        # Customer 5: Has both old and recent orders - should NOT be deleted
        c5 = Customer.objects.create(name="C5", email="c5@example.com")
        c5.created_at = timezone.now() - timedelta(days=500)
        c5.save()
        old_order = Order.objects.create(customer=c5, total_amount=15.00)
        old_order.order_date = timezone.now() - timedelta(days=450)
        old_order.save()
        old_order.products.add(self.product1)
        
        recent_order = Order.objects.create(customer=c5, total_amount=25.00)
        recent_order.order_date = timezone.now() - timedelta(days=100)
        recent_order.save()
        recent_order.products.add(self.product2)
        
        # Run cleanup
        out = StringIO()
        call_command('cleanup_inactive_customers', stdout=out)
        
        # Verify results
        self.assertTrue(Customer.objects.filter(email="c1@example.com").exists())
        self.assertFalse(Customer.objects.filter(email="c2@example.com").exists())
        self.assertFalse(Customer.objects.filter(email="c3@example.com").exists())
        self.assertTrue(Customer.objects.filter(email="c4@example.com").exists())
        self.assertTrue(Customer.objects.filter(email="c5@example.com").exists())
        
        self.assertIn('2 inactive customer(s) deleted', out.getvalue())
