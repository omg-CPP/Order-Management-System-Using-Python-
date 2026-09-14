
# Now we need something that accepts HTTP requests
 
# Python's built-in JSON module: JSON → Python dictionary and Python dictionary → JSON
import json
# Python already has a basic HTTP server
from http.server import BaseHTTPRequestHandler, HTTPServer

# mports our database class
from database import Database
# Imports our business logic
from services import OrderService

# Creates database object
database = Database()
# Creates our service
order_service = OrderService(database)

# This class handles incoming HTTP requests
class RequestHandler(BaseHTTPRequestHandler):
    # When a client sends POST /orders
    def do_POST(self):
        # checking the end-point
        if self.path != "/orders":
            self.send_response(404) # Not Found
            self.end_headers()
            return
        # suppose a client send this JSON
        # {
        #     "customer_name": "Rahul",
        #     "items": [
        #         {
        #             "menu_item_id": 1,
        #             "quantity": 2
        #         }
        #     ]
        # }
        # This is sent over HTTP as bytes
        # Gets the size of the request body
        content_length = int(self.headers.get("Content-Length", 0))

        # Read it
        body = self.rfile.read(content_length)

        # Convert JSON to Python
        data = json.loads(body.decode("utf-8"))
        # print(type(data)) # -> dict

        customer_name = data["customer_name"]
        items = data["items"]


        try:

            order = order_service.place_order(customer_name, items)


            response = {
                "message": "Order placed successfully",
                "order_id": order.id,
                "customer_name": order.customer_name,
                "total_price": order.total_price,
                "status": order.status
            }

            # self.send_response(200) -> 200 OK Standard success response for GET, PUT, or POST requests
            self.send_response(201) # 201 Created New recored was successfully created

            # Adds an HTTP Header telling the client what kind of data is in the response body
            self.send_header(
                "Content-Type",
                "application/json"
            )

            self.end_headers()

            # converts Python dictionary to JSON
            self.wfile.write(json.dumps(response).encode())


        except ValueError as error:

            response = {
                "error": str(error)
            }

            self.send_response(400) # 400 Bad Request
            # The server cannot process the request due to invalid syntax, bad JSON formatting, or missing required fields.

            self.send_header(
                "Content-Type",
                "application/json"
            )

            self.end_headers()

            self.wfile.write(json.dumps(response).encode())


# Function responsible for starting our server
def run_server():
    # Our application runs at: http://localhost:8000
    server = HTTPServer(("localhost", 8000), RequestHandler)

    print("Server running on http://localhost:8000")
    # Keep the server running and continuously wait for requests
    server.serve_forever()


run_server()


