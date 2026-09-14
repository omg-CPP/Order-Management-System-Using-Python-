
# Now comes the business layer

# Repository asks: "How do I talk to MySQL?"
# Service asks: "What should happen when a customer places an order?"

from models import Order, OrderItem
from repositories import MenuItemRepository, OrderRepository


class OrderService:

    def __init__(self, database):
        self.database = database
        self.menu_repository = MenuItemRepository()
        self.order_repository = OrderRepository()


    def place_order(self, customer_name, items):

        connection = self.database.connect()

        try:
            total_price = 0
            order_items = []
            # items = [
            #     {"menu_item_id": 1, "quantity": 2},
            #     {"menu_item_id": 3, "quantity": 1}
            # ]
            for item in items:

                menu_item_id = item["menu_item_id"]
                quantity = item["quantity"]

                # menu_item is an object of class MenuItem
                menu_item = self.menu_repository.get_by_id(connection, menu_item_id)

                if menu_item is None:
                    raise ValueError("Menu item does not exist")

                if menu_item.available_stock < quantity:
                    raise ValueError("Not enough stock")

                self.menu_repository.update_stock(connection, menu_item_id, -quantity)

                item_total = menu_item.price * quantity
                total_price = total_price + item_total

                order_item = OrderItem(menu_item_id, quantity, menu_item.price)
                # list of objects
                order_items.append(order_item)


            order_id = self.order_repository.save_order(connection, customer_name, total_price, "PLACED")


            for order_item in order_items:

                self.order_repository.save_order_item(connection, order_id, order_item.menu_item_id, 
                    order_item.quantity, order_item.price_per_unit)


            self.database.commit()

            order = Order(order_id, customer_name, order_items, total_price, "PLACED")

            return order


        except Exception as error:
            self.database.rollback()
            raise error

        # Whether the operation succeeds or fails
        finally:
            self.database.close()