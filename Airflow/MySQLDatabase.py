import pymysql
import pandas as pd

class MySQLConnector:
    def __init__(self):
        """
        Initialize the MySQLConnector object and establish a connection to the MySQL database.
        """
        self.host = "scisketch-finetuning.cha8ies4obs2.us-east-1.rds.amazonaws.com"
        self.user = "admin"
        self.password = "12345678"  # Replace with your actual password
        self.database = "scisketch"
        self.port = 3306
        self.ssl_ca = "global-bundle.pem"  # Update with the actual path if needed
        self.connection = None
        self.connect()

    def connect(self):
        """Establishes the connection to the MySQL database."""
        try:
            self.connection = pymysql.connect(
                host=self.host,
                user=self.user,
                passwd=self.password,
                database=self.database,
                port=self.port,
                ssl_ca=self.ssl_ca
            )
            print("Connected to the MySQL database.")
        except pymysql.MySQLError as e:
            print(f"Error connecting to MySQL: {e}")
            raise

    def close_connection(self):
        """Closes the connection to the MySQL database."""
        if self.connection:
            self.connection.close()
            print("Connection closed.")

    def upload_dataframe(self, df, table_name):
        """
        Uploads a Pandas DataFrame to a new table in the MySQL database.
        :param df: Pandas DataFrame to upload
        :param table_name: Name of the new table to create in the database
        """
        try:
            with self.connection.cursor() as cursor:
                # Generate the SQL statement for creating a table
                columns = ', '.join(f"`{col}` VARCHAR(255)" for col in df.columns)
                create_table_sql = f"CREATE TABLE IF NOT EXISTS `{table_name}` ({columns});"
                cursor.execute(create_table_sql)

                # Insert DataFrame rows into the table
                for _, row in df.iterrows():
                    values = ', '.join(f"'{str(val)}'" for val in row)
                    insert_row_sql = f"INSERT INTO `{table_name}` VALUES ({values});"
                    cursor.execute(insert_row_sql)

                # Commit the transaction
                self.connection.commit()
                print(f"DataFrame uploaded successfully to the table `{table_name}`.")
        except pymysql.MySQLError as e:
            print(f"Error uploading DataFrame to MySQL: {e}")
            self.connection.rollback()
    def list_tables(self):
        """
        Retrieves and returns a list of all table names in the connected database.
        :return: List of table names
        """
        try:
            with self.connection.cursor() as cursor:
                cursor.execute("SHOW TABLES;")
                tables = cursor.fetchall()
                table_names = [table[0] for table in tables]
                return table_names
        except pymysql.MySQLError as e:
            print(f"Error fetching table names: {e}")
            return []

    def preview_table(self, table_name, limit=5):
        """
        Previews the content of a specified table.
        :param table_name: Name of the table to preview
        :param limit: Number of rows to preview, default is 5
        :return: Pandas DataFrame containing the preview of the table
        """
        try:
            query = f"SELECT * FROM `{table_name}` LIMIT {limit};"
            df = pd.read_sql(query, self.connection)
            return df
        except pymysql.MySQLError as e:
            print(f"Error previewing table `{table_name}`: {e}")
            return pd.DataFrame()

    def __del__(self):
        """Ensures the connection is closed when the object is deleted."""
        self.close_connection()

# Example usage
if __name__ == "__main__":
    # Initialize the MySQLConnector (connection details are hardcoded)
    db_connector = MySQLConnector()

    # Example DataFrame
    data = {'column1': ['value1', 'value2'], 'column2': ['value3', 'value4']}
    df = pd.DataFrame(data)

    # Upload DataFrame to a new table
    db_connector.upload_dataframe(df, "new_table_name")

     # List all tables in the database
    tables = db_connector.list_tables()
    print("Tables in the database:", tables)

    # Preview the content of a specified table
    preview_df = db_connector.preview_table("new_table_name")
    print("Preview of the table 'new_table_name':")
    print(preview_df)
