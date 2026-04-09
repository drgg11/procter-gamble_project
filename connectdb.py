import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL")

if DATABASE_URL:
    connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
    engine = create_engine(DATABASE_URL, connect_args=connect_args)
else:
    import pyodbc
    connection_string = (
        r'Driver={ODBC Driver 18 for SQL Server};'
        r'Server=DESKTOP-8OEIM3E;'
        r'Database=project_pg;'
        r'Trusted_Connection=yes;'
        r'TrustServerCertificate=yes;'
    )
    engine = create_engine(f'mssql+pyodbc:///?odbc_connect={connection_string}', echo=False)

Session = sessionmaker(bind=engine)

def get_session():
    return Session()

conn = engine