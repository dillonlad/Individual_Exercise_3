# 1. Import the PayPal SDK client that was created in `Set up Server-Side SDK`.

from app.new_paypal import PayPalClient
from paypalcheckoutsdk.orders import OrdersCreateRequest


class CreateOrder(PayPalClient):
  def __init__(self):
    super().__init__()

  #2. Set up your server to receive a call from the client
  """ This is the sample function to create an order. It uses the
    JSON body returned by buildRequestBody() to create an order."""

  def create_order(self, payment_create, debug=False):
    request = OrdersCreateRequest()
    request.prefer('return=representation')
    #3. Call PayPal to set up a transaction
    request.request_body(payment_create)
    response = self.client.execute(request)
    if debug:
      print('Status Code: ', response.status_code)
      print('Status: ', response.result.status)
      print('Order ID: ', response.result.id)
      print('Intent: ', response.result.intent)
      print('Links:')
      for link in response.result.links:
        print('\t{}: {}\tCall Type: {}'.format(link.rel, link.href, link.method))
      print('Total Amount: {} {}'.format(response.result.purchase_units[0].amount.currency_code,
                         response.result.purchase_units[0].amount.value))

    return response