import fastapi as fa
from pydantic import BaseModel
from sqlalchemy import Column, String, Text, Integer, DECIMAL, ForeignKey
from sqlalchemy.orm import declarative_base, relationship
from connectdb import engine, get_session


Base = declarative_base()

class Identifiers(Base):
    __tablename__ = 'Identifiers'
    identifier_name = Column(String(255), primary_key=True)
    description = Column(Text)
    identifier_type = Column(String(255))

class Countries(Base):
    __tablename__ = 'Countries'
    name = Column(String(255), primary_key=True)
    iso_code = Column(String(255))
    short_code = Column(String(255))

class ConsumerUnits(Base):
    __tablename__ = 'ConsumerUnits'
    number_of_consumers = Column(Integer, primary_key=True)
    country_name = Column(String(255), ForeignKey('Countries.name'), primary_key=True)

class Ownership(Base):
    __tablename__ = 'Ownership'
    identifier_name = Column(String(255), ForeignKey('Identifiers.identifier_name'), primary_key=True)
    originator_first_name = Column(String(255))
    originator_last_name = Column(String(255))
    user_id_tnumber = Column(String(255), primary_key=True)
    user_id_intranet = Column(String(255))
    email = Column(String(255))
    owner_first_name = Column(String(255))
    owner_last_name = Column(String(255))

class Relationships(Base):
    __tablename__ = 'Relationships'
    from_identifier_name = Column(String(255), ForeignKey('Identifiers.identifier_name'), primary_key=True)
    to_identifier_name = Column(String(255), ForeignKey('Identifiers.identifier_name'), primary_key=True)
    relationship_name = Column(String(255))

class Characteristics(Base):
    __tablename__ = 'Characteristics'
    master_name = Column(String(255), primary_key=True)
    name = Column(String(255), primary_key=True)
    specifics = Column(String(255))
    action_required = Column(String(255))
    report_type = Column(String(255))
    data_type = Column(String(255))
    lower_routine_release_limit = Column(DECIMAL(10, 2))
    lower_limit = Column(DECIMAL(10, 2))
    lower_target = Column(DECIMAL(10, 2))
    target = Column(DECIMAL(10, 2))
    upper_target = Column(DECIMAL(10, 2))
    upper_limit = Column(DECIMAL(10, 2))
    upper_routine_release_limit = Column(DECIMAL(10, 2))
    test_frequency = Column(Integer)
    precision = Column(Integer)
    engineering_unit = Column(String(255))

class IdentifierCharacteristics(Base):
    __tablename__ = 'IdentifierCharacteristics'
    identifier_name = Column(String(255), ForeignKey('Identifiers.identifier_name'), primary_key=True)
    master_name = Column(String(255), primary_key=True)
    characteristic_name = Column(String(255), primary_key=True)
    __table_args__ = {'schema': None}

app = fa.FastAPI()

class EfficiencyRequest(BaseModel):
    speed: float
    downtime: float
    quality_rate: float
    utilization_rate: float

def calculate_efficiency(speed: float, downtime: float, quality_rate: float, utilization_rate: float) -> float:
    return (speed * downtime * quality_rate * utilization_rate * 100) / 60

@app.post("/calculate_efficiency")
def calculate_efficiency_endpoint(data: EfficiencyRequest):
    if data.quality_rate < 0 or data.quality_rate > 1 or data.utilization_rate < 0 or data.utilization_rate > 1:
        raise fa.HTTPException(status_code=400, detail="Quality rate and utilization rate must be between 0 and 1")
    if data.speed < 0 or data.downtime < 0:
        raise fa.HTTPException(status_code=400, detail="Speed and downtime must be non-negative")
    return {"efficiency": calculate_efficiency(data.speed, data.downtime, data.quality_rate, data.utilization_rate)}


def create_tables():
    try:
        Base.metadata.create_all(engine)
        print('Tables created (or already exist).')
    except Exception as e:
        print(f'Table creation failed: {e}')

def insert_data():
    session = get_session()
    try:
        if session.query(Identifiers).count() > 0:
            print('Data already exists, skipping inserts.')
            return

        # Insert Identifiers
        session.bulk_insert_mappings(Identifiers, identifiers_data)

        # Insert Countries
        session.bulk_insert_mappings(Countries, countries_data)

        # Insert ConsumerUnits
        session.bulk_insert_mappings(ConsumerUnits, consumer_units_data)

        # Insert Ownership
        session.bulk_insert_mappings(Ownership, ownership_data)

        # Insert Relationships
        session.bulk_insert_mappings(Relationships, relationships_data)

        # Characteristics data
        session.bulk_insert_mappings(Characteristics, characteristics_data)

        # IdentifierCharacteristics data
        session.bulk_insert_mappings(IdentifierCharacteristics, identifier_characteristics_data)

        session.commit()
        print('Data inserted successfully.')
    except Exception as e:
        session.rollback()
        print(f'Error inserting data: {e}')
        raise
    finally:
        session.close()

if __name__ == '__main__':
    create_tables()
    print('Tables created. App will display data from the database.')
    
    # Restore data from git commit if tables are empty
    session = get_session()
    if session.query(Identifiers).count() == 0:
        print('Database is empty, restoring data...')
        # Restore Identifiers from git commit
        identifiers = [
            Identifiers(identifier_name='Product_A', description='Main Product A', identifier_type='Product'),
            Identifiers(identifier_name='Product_B', description='Main Product B', identifier_type='Product'),
            Identifiers(identifier_name='Category_1', description='Product Category 1', identifier_type='Category'),
        ]
        session.add_all(identifiers)
        
        # Restore Countries
        countries = [
            Countries(name='United States', iso_code='US', short_code='USA'),
            Countries(name='Canada', iso_code='CA', short_code='CAN'),
        ]
        session.add_all(countries)
        
        session.commit()
        print('Data restored successfully.')
    else:
        print(f'Found {session.query(Identifiers).count()} existing Identifiers in database.')
    
    session.close()
