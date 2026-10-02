import mysql.connector
from mysql.connector import Error
# Remove: import bcrypt (no longer needed)

class DBManager:
    def __init__(self, host="localhost", user="root", password="", database="space_invaders_db"):
        self.config = {
            "host": host,
            "user": user,
            "password": password,
            "database": database
        }
        self.connection = None
        self.connect()

    def connect(self):
        """Establishes or re-establishes the connection to MySQL."""
        try:
            if self.connection is None or not self.connection.is_connected():
                self.connection = mysql.connector.connect(**self.config)
        except Error as e:
            print(f"Error connecting to MySQL Database: {e}")

    def get_cursor(self, dictionary=False):
        """Ensures active connection and returns a cursor."""
        self.connect()
        if self.connection and self.connection.is_connected():
            return self.connection.cursor(dictionary=dictionary)
        return None

    # ==================== AUTHENTICATION METHODS ====================

    def register_user(self, name, username, password):
        """Registers a new user with plain text password."""
        cursor = self.get_cursor()
        if not cursor:
            return False, "Could not connect to database."

        try:
            # Check if username already exists
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                cursor.close()
                return False, "Username already exists!"

            # Insert user into database using plain text password directly
            query = "INSERT INTO users (name, username, password) VALUES (%s, %s, %s)"
            cursor.execute(query, (name, username, password))
            self.connection.commit()
            cursor.close()
            return True, "Registration successful!"

        except Error as err:
            if cursor:
                cursor.close()
            return False, f"Database error: {err}"

    def login_user(self, username, password):
        """Authenticates user credentials using plain text comparison."""
        cursor = self.get_cursor(dictionary=True)
        if not cursor:
            return False, "Could not connect to database."

        try:
            query = "SELECT * FROM users WHERE username = %s"
            cursor.execute(query, (username,))
            user = cursor.fetchone()
            cursor.close()

            # Compare typed password directly with plain text password in database
            if user and user['password'] == password:
                return True, user
            return False, "Invalid username or password."

        except Error as err:
            if cursor:
                cursor.close()
            return False, f"Database error: {err}"

    def close(self):
        """Closes the MySQL database connection cleanly."""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("MySQL connection closed.")