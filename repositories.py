# The layer responsible for talking to the database.
# The service should not directly write SQL.
#   services.py
#      ↓
#  repositories.py
#      ↓
#    MySQL


from models import MenuItem, OrderItem

# this deals with menu_items table
class MenuItemRepository:

    # Find menu item whose ID is item_id
    def get_by_id(self, connection, item_id):

        # A cursor is basically an object that allows Python to execute SQL
        cursor = connection.cursor(dictionary=True)

        query = """
        SELECT id, name, price, available_stock FROM menu_items
        WHERE id = %s
        """

        cursor.execute(query, (item_id,))

        # Gets one row from the database
        row = cursor.fetchone()

        cursor.close()

        if row is None:
            return None

        # MySQL row -> MenuItem object
        item = MenuItem(row["id"], row["name"], float(row["price"]), row["available_stock"])
        return item


    def update_stock(self, connection, item_id, quantity):

        cursor = connection.cursor()

        query = """
        UPDATE menu_items
        SET available_stock = available_stock + %s
        WHERE id = %s
        """

        cursor.execute(query, (quantity, item_id))

        cursor.close()

# This handles orders and order_items tables
class OrderRepository:
    # orders table
    def save_order(self, connection, customer_name, total_price, status):

        cursor = connection.cursor()

        query = """
        INSERT INTO orders(customer_name, total_price, status) VALUES 
        (%s, %s, %s)
        """

        cursor.execute(query, (customer_name, total_price, status))

        order_id = cursor.lastrowid

        cursor.close()

        return order_id

    # order_items table
    def save_order_item(self, connection, order_id, menu_item_id, quantity, price_per_unit):

        cursor = connection.cursor()

        query = """
        INSERT INTO order_items(order_id, menu_item_id, quantity, price_per_unit) VALUES 
        (%s, %s, %s, %s)
        """

        cursor.execute(query, (order_id, menu_item_id, quantity, price_per_unit))

        cursor.close()


# dictionary=True makes the returned row look like:
# {
#     "id": 1,
#     "name": "Burger",
#     "price": 100,
#     "available_stock": 10
# }

# cursor.execute(query, (item_id,))
# item_id = 1
# The query effectively becomes:

# SELECT id, name, price, available_stock FROM menu_items
# WHERE id = 1;



