import pyodbc


conn = pyodbc.connect(
    'DRIVER={ODBC Driver 17 for SQL Server};'
    'SERVER=DESKTOP-8OEIM3E;'       # ex: localhost\SQLEXPRESS
    'DATABASE=project_pg;'                
    'Trusted_Connection=yes;'        # Windows Authentication
)
