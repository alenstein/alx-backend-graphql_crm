import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

def log_crm_heartbeat():
    """Logs a heartbeat message to a file."""
    with open("/tmp/crm_heartbeat_log.txt", "a") as f:
        now = datetime.datetime.now()
        f.write(f"{now.strftime('%d/%m/%Y-%H:%M:%S')} CRM is alive\n")

    try:
        transport = RequestsHTTPTransport(url="http://localhost:8000/graphql")
        client = Client(transport=transport, fetch_schema_from_transport=True)
        query = gql("query { hello }" )
        result = client.execute(query)
        with open("/tmp/crm_heartbeat_log.txt", "a") as f:
            f.write(f"{now.strftime('%d/%m/%Y-%H:%M:%S')} GraphQL endpoint is responsive: {result}\n")
    except Exception as e:
        with open("/tmp/crm_heartbeat_log.txt", "a") as f:
            now = datetime.datetime.now()
            f.write(f"{now.strftime('%d/%m/%Y-%H:%M:%S')} Error querying GraphQL: {e}\n")

def update_low_stock():
    """Executes the UpdateLowStockProducts mutation and logs the result."""
    transport = RequestsHTTPTransport(url="http://localhost:8000/graphql")
    client = Client(transport=transport, fetch_schema_from_transport=True)
    
    mutation_str = """
        mutation {
          updateLowStockProducts {
            updatedProducts {
              name
              stock
            }
            message
          }
        }
    """
    mutation = gql(mutation_str)
    
    try:
        result = client.execute(mutation)
        updated_products = result['updateLowStockProducts']['updatedProducts']
        message = result['updateLowStockProducts']['message']
        
        with open("/tmp/low_stock_updates_log.txt", "a") as f:
            now = datetime.datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
            f.write(f"[{now}] {message}\n")
            for product in updated_products:
                f.write(f"  - Product: {product['name']}, New Stock: {product['stock']}\n")
                
    except Exception as e:
        with open("/tmp/low_stock_updates_log.txt", "a") as f:
            now = datetime.datetime.now().strftime('%d/%m/%Y-%H:%M:%S')
            f.write(f"[{now}] Error executing mutation: {e}\n")
