# Order Management System (OMS)

A simple **Order Management System** built using Python, MySQL, and HTTP APIs. The project follows a **Monolithic Architecture** with a **Layered Architecture** to separate database access, business logic, and API handling.

## Features

* Create and place customer orders
* Store menu items and their prices
* Check available stock
* Automatically update stock after placing an order
* Calculate the total order price
* Store orders and order items in MySQL
* Handle API requests using Python's built-in HTTP server
* Return responses in JSON format
* Use repository and service layers for better separation of responsibilities

## Technologies Used

* **Python**
* **MySQL**
* **mysql-connector-python**
* **HTTP / REST-style API**
* **JSON**
* **Thunder Client / Postman** for API testing
* **VS Code**

## Project Structure

```text
OMS/
│
├── schema.sql
├── database.py
├── models.py
├── repositories.py
├── services.py
├── main.py
├── requirements.txt
└── README.md
```

## Architecture

The project follows a layered architecture:

```text
Client / Thunder Client
        ↓
    main.py
        ↓
   services.py
        ↓
 repositories.py
        ↓
   database.py
        ↓
      MySQL
```

### Layers

**main.py**

* Handles HTTP requests and responses
* Receives order data in JSON format
* Sends the request to the service layer

**services.py**

* Contains the main business logic
* Checks stock availability
* Calculates the order total
* Updates stock
* Creates the order

**repositories.py**

* Communicates with MySQL
* Reads menu item information
* Updates stock
* Saves orders and order items

**database.py**

* Creates the MySQL connection
* Handles commit and rollback
* Closes the database connection

**models.py**

* Defines Python classes representing menu items and orders

**schema.sql**

* Creates the database and required tables
* Inserts initial menu items

## Database

The project uses a MySQL database named:

```text
restaurant_db
```

The main tables are:

```text
menu_items
orders
order_items
```

### Sample Menu

| ID | Item   |  Price | Stock |
| -: | ------ | -----: | ----: |
|  1 | Burger | 100.00 |    10 |
|  2 | Pizza  | 200.00 |    10 |
|  3 | Coke   |  50.00 |    20 |

## Setup

### 1. Clone the repository

```bash
git clone <your-github-repository-url>
```

Move into the project directory:

```bash
cd OMS
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure MySQL

Make sure the MySQL server is running.

Open `schema.sql` in MySQL Workbench or another MySQL client and execute it.

This creates the database:

```text
restaurant_db
```

and the required tables.

### 5. Configure the database connection

Open:

```text
database.py
```

Update the MySQL password:

```python
self.connection = mysql.connector.connect(
    host="localhost",
    user="root",
    password="YOUR_PASSWORD",
    database="restaurant_db"
)
```

Replace `YOUR_PASSWORD` with your MySQL password.

## Running the Application

Start the Python API server:

```bash
python main.py
```

The server will run at:

```text
http://localhost:8000
```

You should see:

```text
Server running on http://localhost:8000
```

## API Testing

The API can be tested using **Thunder Client**, **Postman**, or another HTTP client.

### Place an Order

**Method:**

```text
POST
```

**Endpoint:**

```text
http://localhost:8000/orders
```

### Request Body

Select:

```text
Body → JSON
```

and send:

```json
{
    "customer_name": "Rahul",
    "items": [
        {
            "menu_item_id": 1,
            "quantity": 2
        }
    ]
}
```

### Response

A successful request returns a response similar to:

```json
{
    "message": "Order placed successfully",
    "order_id": 1,
    "customer_name": "Rahul",
    "total_price": 200.0,
    "status": "PLACED"
}
```

## Order Calculation

For example, if a customer orders:

```text
Burger × 2
```

and the Burger price is:

```text
₹100
```

the total is:

```text
₹100 × 2 = ₹200
```

For multiple items, the service layer calculates the total for each item and adds them together.

## Stock Management

When an order is successfully placed, the ordered quantity is deducted from the available stock.

For example:

```text
Initial Burger Stock = 10
Ordered Quantity     = 2
Remaining Stock      = 8
```

If the requested quantity is greater than the available stock, the order is rejected.

## Transaction Handling

The application uses:

* **COMMIT** when an order is successfully created
* **ROLLBACK** when an error occurs

This helps prevent incomplete database updates.

## Example Flow

```text
1. Client sends POST /orders
             ↓
2. main.py receives JSON request
             ↓
3. OrderService processes the order
             ↓
4. Repository checks menu item and stock
             ↓
5. Stock is updated
             ↓
6. Order is saved in MySQL
             ↓
7. Transaction is committed
             ↓
8. JSON response is returned
```

## Author

**Om Gupta**


