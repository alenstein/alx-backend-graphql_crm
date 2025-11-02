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
