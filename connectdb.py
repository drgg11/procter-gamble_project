import pyodbc

connection_string = (
    r'Driver={SQL Server};'
    r'Server=DESKTOP-EIE92NK;'
    r'Database=database;'
    r'Trusted_Connection=yes;'
)

try:
    conn = pyodbc.connect(connection_string, timeout=5)
    print('Database connection successful')
except pyodbc.Error as error:
    print('Database connection failed:')
    print(error)
    conn = None