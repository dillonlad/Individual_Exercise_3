from paypalcheckoutsdk.core import PayPalHttpClient, LiveEnvironment

import sys

class PayPalClient:
    def __init__(self):
        self.client_id = "AX1xZ5LS2EKdjzXGX5s9pqscRnp_HXF_DYoUarP40589iY4891E4bGL0OwllD8JSBwEQ6AWgkBDPvs5A"
        self.client_secret = "EDdiEGaGzpXfTXIt5zgmDr1VW_-y7K5NzOedZSQ6uEqjjAhyEgEeWSDLpqiJNVt9LagWRB66GobPOwCt"

        """Set up and return PayPal Python SDK environment with PayPal access credentials.
           This sample uses SandboxEnvironment. In production, use LiveEnvironment."""

        self.environment = LiveEnvironment(client_id=self.client_id, client_secret=self.client_secret)

        """ Returns PayPal HTTP client instance with environment that has access
            credentials context. Use this instance to invoke PayPal APIs, provided the
            credentials have access. """
        self.client = PayPalHttpClient(self.environment)

    def object_to_json(self, json_data):
        """
        Function to print all json data in an organized readable manner
        """
        result = {}
        if sys.version_info[0] < 3:
            itr = json_data.__dict__.iteritems()
        else:
            itr = json_data.__dict__.items()
        for key,value in itr:
            # Skip internal attributes.
            if key.startswith("__"):
                continue
            result[key] = self.array_to_json_array(value) if isinstance(value, list) else\
                        self.object_to_json(value) if not self.is_primittive(value) else\
                         value
        return result;

    def array_to_json_array(self, json_array):
        result =[]
        if isinstance(json_array, list):
            for item in json_array:
                result.append(self.object_to_json(item) if  not self.is_primittive(item) \
                              else self.array_to_json_array(item) if isinstance(item, list) else item)
        return result;

    def is_primittive(self, data):
        return isinstance(data, str) or isinstance(data, unicode) or isinstance(data, int)