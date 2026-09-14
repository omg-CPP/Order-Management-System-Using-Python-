CREATE DATABASE IF NOT EXISTS restaurant_db;
USE restaurant_db;


CREATE TABLE IF NOT EXISTS menu_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100),
    price DECIMAL(10, 2),
    available_stock INT
);


CREATE TABLE IF NOT EXISTS orders (
    id INT AUTO_INCREMENT PRIMARY KEY,
    customer_name VARCHAR(100),
    total_price DECIMAL(10, 2),
    status VARCHAR(50)
);


CREATE TABLE IF NOT EXISTS order_items (
    id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT,
    menu_item_id INT,
    quantity INT,
    price_per_unit DECIMAL(10, 2)
);


INSERT INTO menu_items(name, price, available_stock) VALUES
('Burger', 100.00, 10),
('Pizza', 200.00, 10),
('Coke', 50.00, 20);







