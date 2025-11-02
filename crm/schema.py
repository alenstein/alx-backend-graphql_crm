
import graphene
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from .models import Customer, Product, Order
from .filters import CustomerFilter, ProductFilter, OrderFilter
import re
from django.db import transaction

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer
        fields = ("id", "name", "email", "phone", "created_at")
        interfaces = (graphene.relay.Node,)

class ProductType(DjangoObjectType):
    class Meta:
        model = Product
        fields = ("id", "name", "price", "stock")
        interfaces = (graphene.relay.Node,)

class OrderType(DjangoObjectType):
    class Meta:
        model = Order
        fields = ("id", "customer", "products", "order_date", "total_amount")
        interfaces = (graphene.relay.Node,)

class Query(graphene.ObjectType):
    all_customers = DjangoFilterConnectionField(CustomerType, filterset_class=CustomerFilter)
    all_products = DjangoFilterConnectionField(ProductType, filterset_class=ProductFilter)
    all_orders = DjangoFilterConnectionField(OrderType, filterset_class=OrderFilter)

class CreateCustomer(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        email = graphene.String(required=True)
        phone = graphene.String()

    customer = graphene.Field(CustomerType)
    message = graphene.String()

    def mutate(self, info, name, email, phone=None):
        if Customer.objects.filter(email=email).exists():
            raise Exception("Email already exists.")
        if phone and not re.match(r"^(\+1)?\d{10}$|^\d{3}-\d{3}-\d{4}$", phone):
            raise Exception("Invalid phone number format.")
        
        customer = Customer(name=name, email=email, phone=phone)
        customer.save()
        return CreateCustomer(customer=customer, message="Customer created successfully.")

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        customers_data = graphene.List(graphene.InputObjectType("CustomerInput", {
            "name": graphene.String(required=True),
            "email": graphene.String(required=True),
            "phone": graphene.String(),
        }))

    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

    def mutate(self, info, customers_data):
        created_customers = []
        error_list = []
        with transaction.atomic():
            for data in customers_data:
                try:
                    if Customer.objects.filter(email=data.email).exists():
                        raise Exception(f"Email {data.email} already exists.")
                    if data.phone and not re.match(r"^(\+1)?\d{10}$|^\d{3}-\d{3}-\d{4}$", data.phone):
                        raise Exception(f"Invalid phone number format for {data.email}.")
                    
                    customer = Customer(name=data.name, email=data.email, phone=data.phone)
                    customer.save()
                    created_customers.append(customer)
                except Exception as e:
                    error_list.append(str(e))
        return BulkCreateCustomers(customers=created_customers, errors=error_list)

class CreateProduct(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        price = graphene.Decimal(required=True)
        stock = graphene.Int()

    product = graphene.Field(ProductType)

    def mutate(self, info, name, price, stock=0):
        if price <= 0:
            raise Exception("Price must be positive.")
        if stock < 0:
            raise Exception("Stock cannot be negative.")
        
        product = Product(name=name, price=price, stock=stock)
        product.save()
        return CreateProduct(product=product)

class CreateOrder(graphene.Mutation):
    class Arguments:
        customer_id = graphene.ID(required=True)
        product_ids = graphene.List(graphene.ID, required=True)

    order = graphene.Field(OrderType)

    def mutate(self, info, customer_id, product_ids):
        try:
            customer = Customer.objects.get(pk=customer_id)
        except Customer.DoesNotExist:
            raise Exception("Invalid customer ID.")

        if not product_ids:
            raise Exception("At least one product must be selected.")

        products = Product.objects.filter(pk__in=product_ids)
        if len(products) != len(product_ids):
            raise Exception("Invalid product ID(s).")

        total_amount = sum(p.price for p in products)

        order = Order(customer=customer, total_amount=total_amount)
        order.save()
        order.products.set(products)
        return CreateOrder(order=order)

class UpdateLowStockProducts(graphene.Mutation):
    updated_products = graphene.List(ProductType)
    message = graphene.String()

    @transaction.atomic
    def mutate(self, info):
        low_stock_products = Product.objects.filter(stock__lt=10)
        updated_products_list = []
        for product in low_stock_products:
            product.stock += 10
            product.save()
            updated_products_list.append(product)
        
        message = f"Successfully updated {len(updated_products_list)} low-stock products."
        return UpdateLowStockProducts(updated_products=updated_products_list, message=message)

class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
    update_low_stock_products = UpdateLowStockProducts.Field()
