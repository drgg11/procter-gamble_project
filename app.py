import pyodbc
import tkinter as tk
from tkinter import ttk, messagebox

# Database connection and query classes
class DatabaseConnection:
    def __init__(self, connection_string):
        self.connection_string = connection_string
        self.connection = None

    def connect(self):
        try:
            self.connection = pyodbc.connect(self.connection_string)
            print("Connection successful!")
        except pyodbc.Error as ex:
            print(f"Error: {ex}")
            self.connection = None

    def close(self):
        if self.connection:
            self.connection.close()

class DataQuery:
    def __init__(self, db_connection):
        self.db_connection = db_connection

    def fetch_all(self, table_name):
        cursor = self.db_connection.connection.cursor()
        cursor.execute(f"SELECT * FROM {table_name}")
        return cursor.fetchall()

    def insert_identifier(self, identifier_name, description, identifier_type):
        cursor = self.db_connection.connection.cursor()
        cursor.execute("""
            INSERT INTO Identifiers (identifier_name, description, identifier_type)
            VALUES (?, ?, ?)
        """, (identifier_name, description, identifier_type))
        self.db_connection.connection.commit()

    def delete_dependencies(self, table_name, identifier_column, identifier_value):
        cursor = self.db_connection.connection.cursor()

        if table_name == "Identifiers":
            cursor.execute("DELETE FROM Ownership WHERE identifier_name = ?", (identifier_value,))
            cursor.execute("DELETE FROM Relationships WHERE from_identifier_name = ? OR to_identifier_name = ?", (identifier_value, identifier_value))
            cursor.execute("DELETE FROM IdentifierCharacteristics WHERE identifier_name = ?", (identifier_value,))

        if table_name == "Countries":
            cursor.execute("DELETE FROM ConsumerUnits WHERE country_name = ?", (identifier_value,))

        self.db_connection.connection.commit()

    def delete_entry(self, table_name, identifier_column, identifier_value):
        self.delete_dependencies(table_name, identifier_column, identifier_value)
        cursor = self.db_connection.connection.cursor()
        cursor.execute(f"DELETE FROM {table_name} WHERE {identifier_column} = ?", (identifier_value,))
        self.db_connection.connection.commit()

# Tkinter application class
class Application:
    def __init__(self, root, db_connection):
        self.root = root
        self.db_connection = db_connection
        self.notebook = ttk.Notebook(root)
        self.create_tabs()
        self.notebook.pack(expand=1, fill='both')

    def create_tabs(self):
        self.create_identifiers_tab()
        self.create_generic_tab("Countries", ["Name", "ISO Code", "Short Code"], "name")
        self.create_generic_tab("ConsumerUnits", ["Number of Consumers", "Country Name"], "country_name")
        self.create_generic_tab("Ownership", ["Identifier Name", "Originator First Name", "User ID"], "identifier_name")
        self.create_generic_tab("Relationships", ["From Identifier", "To Identifier", "Relationship"], "from_identifier_name")
        self.create_generic_tab("Characteristics", ["Master Name", "Name", "Specifics"], "master_name")
        self.create_generic_tab("IdentifierCharacteristics", ["Identifier Name", "Master Name", "Characteristic Name"], "identifier_name")

    def create_identifiers_tab(self):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text="Identifiers")

        self.identifier_tree = ttk.Treeview(frame, columns=('Identifier', 'Description', 'Type'), show='headings')
        self.identifier_tree.heading('Identifier', text='Identifier')
        self.identifier_tree.heading('Description', text='Description')
        self.identifier_tree.heading('Type', text='Type')
        self.identifier_tree.pack(expand=True, fill='both')

        self.fetch_identifiers()

        entry_frame = ttk.Frame(frame)
        entry_frame.pack(pady=10)

        ttk.Label(entry_frame, text="Identifier Name:").grid(row=0, column=0)
        self.identifier_name_entry = ttk.Entry(entry_frame)
        self.identifier_name_entry.grid(row=0, column=1)

        ttk.Label(entry_frame, text="Description:").grid(row=1, column=0)
        self.description_entry = ttk.Entry(entry_frame)
        self.description_entry.grid(row=1, column=1)

        ttk.Label(entry_frame, text="Type:").grid(row=2, column=0)
        self.type_entry = ttk.Entry(entry_frame)
        self.type_entry.grid(row=2, column=1)

        ttk.Button(entry_frame, text="Add Identifier", command=self.add_identifier).grid(row=3, columnspan=2, pady=5)
        ttk.Button(frame, text="Delete Selected", command=lambda: self.delete_entry(self.identifier_tree, "Identifiers", "identifier_name")).pack(pady=5)

    def fetch_identifiers(self):
        data_query = DataQuery(self.db_connection)
        data = data_query.fetch_all("Identifiers")
        for row in data:
            self.identifier_tree.insert("", tk.END, values=[str(item) for item in row])

    def add_identifier(self):
        identifier_name = self.identifier_name_entry.get()
        description = self.description_entry.get()
        identifier_type = self.type_entry.get()

        if identifier_name and description and identifier_type:
            data_query = DataQuery(self.db_connection)
            data_query.insert_identifier(identifier_name, description, identifier_type)
            self.identifier_tree.insert("", tk.END, values=(identifier_name, description, identifier_type))
            self.identifier_name_entry.delete(0, tk.END)
            self.description_entry.delete(0, tk.END)
            self.type_entry.delete(0, tk.END)
        else:
            messagebox.showwarning("Input Error", "All fields are required!")

    def create_generic_tab(self, table_name, columns, identifier_column):
        frame = ttk.Frame(self.notebook)
        self.notebook.add(frame, text=table_name)

        tree = ttk.Treeview(frame, columns=columns, show='headings')
        for col in columns:
            tree.heading(col, text=col)
        tree.pack(expand=True, fill='both')

        data_query = DataQuery(self.db_connection)
        data = data_query.fetch_all(table_name)
        for row in data:
            tree.insert("", tk.END, values=[str(item) for item in row])

        ttk.Button(frame, text="Delete Selected", command=lambda: self.delete_entry(tree, table_name, identifier_column)).pack(pady=5)

    def delete_entry(self, tree, table_name, identifier_column):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showerror("Error", "No item selected")
            return
        item_values = tree.item(selected_item, "values")
        identifier_value = item_values[0]

        data_query = DataQuery(self.db_connection)
        data_query.delete_entry(table_name, identifier_column, identifier_value)
        tree.delete(selected_item)

# Main function to run the application
def run_app():
    connection_string = (
        "Driver={ODBC Driver 17 for SQL Server};"
        "Server=(localdb)\\localhost;"
        "Database=Dummy;"
        "Trusted_Connection=yes;"
    )

    db_connection = DatabaseConnection(connection_string)
    db_connection.connect()

    root = tk.Tk()
    root.title("Database Viewer")
    app = Application(root, db_connection)
    root.mainloop()

    db_connection.close()

if __name__ == "__main__":
    run_app()