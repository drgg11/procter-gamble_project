from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

connection_string = (
    r'Driver={SQL Server};'
    r'Server=DESKTOP-EIE92NK;'
    r'Database=database;'
    r'Trusted_Connection=yes;'
)

engine = create_engine(f'mssql+pyodbc:///?odbc_connect={connection_string}', echo=False)
Session = sessionmaker(bind=engine)

def get_session():
    return Session()

# For backward compatibility, keep conn as engine
conn = engine