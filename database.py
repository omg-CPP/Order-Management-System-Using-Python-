# pip install mysql-connector-python
import mysql.connector
# This imports the MySQL Python library

# Created a class responsible for database operations
class Database:

    def __init__(self):
        self.connection = None

    def connect(self):
        self.connection = mysql.connector.connect(
            host="localhost",
            port=3306,
            user="root",
            password="password",
            database="restaurant_db"
        )

        return self.connection

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def close(self):
        self.connection.close()



# import mysql.connector
# class Database:

#     def __init__(self):
#         self.connection = None

#     def connect(self):
#         self.connection = mysql.connector.connect(
#             host="localhost",
#             port=3306,
#             user="root",
#             password="password",
#             database="restaurant_db"
#         )

#         return self.connection

#     def close(self):
#         self.connection.close()


# database = Database()

# connection = database.connect()

# print("Database connected successfully!")
# # Database connected successfully!

# database.close()


