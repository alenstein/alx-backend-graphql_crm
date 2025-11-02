
from datetime import datetime, timedelta
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# Set up the transport
transport = RequestsHTTPTransport(url="http://localhost:8000/graphql")

# Create a client
client = Client(transport=transport, fetch_schema_from_transport=True)

# Define the query
one_week_ago = datetime.now() - timedelta(days=7)
query_str = f"""
query {{
  orders(orderDate_Gte: \"{one_week_ago.isoformat()}\") {{
    id
    customer {{
      email
    }}
  }}
}}
"""
query = gql(query_str)

# Execute the query and log the results
try:
    result = client.execute(query)
    with open('/tmp/order_reminders_log.txt', 'a') as f:
        for order in result['orders']:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = f"{timestamp}: Order ID {order['id']}, Customer: {order['customer']['email']}\n"
            f.write(log_entry)
    print("Order reminders processed!")
except Exception as e:
    with open('/tmp/order_reminders_log.txt', 'a') as f:
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_entry = f"{timestamp}: Error querying GraphQL: {e}\n"
        f.write(log_entry)

