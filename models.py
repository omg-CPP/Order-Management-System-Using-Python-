

class MenuItem:

    def __init__(self, id, name, price, available_stock):
        self.id = id
        self.name = name
        self.price = price
        self.available_stock = available_stock


class OrderItem:

    def __init__(self, menu_item_id, quantity, price_per_unit):
        self.menu_item_id = menu_item_id
        self.quantity = quantity
        self.price_per_unit = price_per_unit


class Order:

    def __init__(self, id, customer_name, items, total_price, status):
        self.id = id
        self.customer_name = customer_name
        self.items = items
        self.total_price = total_price
        self.status = status

        