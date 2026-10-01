import mysql.connector
from mysql.connector import Error
import bcrypt

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
        """Registers a new user with hashed password."""
        cursor = self.get_cursor()
        if not cursor:
            return False, "Could not connect to database."

        try:
            # Check if username already exists
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                cursor.close()
                return False, "Username already exists!"

            # Hash password securely
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            # Insert user into database
            query = "INSERT INTO users (name, username, password) VALUES (%s, %s, %s)"
            cursor.execute(query, (name, username, hashed_pw))
            self.connection.commit()
            cursor.close()
            return True, "Registration successful!"

        except Error as err:
            if cursor:
                cursor.close()
            return False, f"Database error: {err}"

    def login_user(self, username, password):
        """Authenticates user credentials."""
        cursor = self.get_cursor(dictionary=True)
        if not cursor:
            return False, "Could not connect to database."

        try:
            query = "SELECT * FROM users WHERE username = %s"
            cursor.execute(query, (username,))
            user = cursor.fetchone()
            cursor.close()

            if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
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