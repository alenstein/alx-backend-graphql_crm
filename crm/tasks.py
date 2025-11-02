from celery import shared_task
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
import datetime

@shared_task
def generate_crm_report():
    """Generates a CRM report and logs it to a file."""
    transport = RequestsHTTPTransport(url="http://localhost:8000/graphql")
    client = Client(transport=transport, fetch_schema_from_transport=True)

    query_str = """
        query {
          allCustomers {
            totalCount
          }
          allOrders {
            totalCount
            edges {
              node {
                totalAmount
              }
            }
          }
        }
    """
    query = gql(query_str)

    try:
        result = client.execute(query)
        customer_count = result['allCustomers']['totalCount']
        order_count = result['allOrders']['totalCount']
        total_revenue = sum(edge['node']['totalAmount'] for edge in result['allOrders']['edges'])

        with open("/tmp/crm_report_log.txt", "a") as f:
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{now} - Report: {customer_count} customers, {order_count} orders, {total_revenue} revenue\n")

    except Exception as e:
        with open("/tmp/crm_report_log.txt", "a") as f:
            now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            f.write(f"{now} - Error generating report: {e}\n")
