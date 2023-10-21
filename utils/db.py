from sqlalchemy import create_engine, orm
from sqlalchemy.orm import sessionmaker
from inspector.models.base import Base


def get_inspect_database_uri():
    username = "kia"
    password = "tlsc"
    host = "localhost"
    db_name = "tlsc"
    return f"postgresql+psycopg2://{username}:{password}@{host}/{db_name}"


def _get_engine(uri: str):
    return create_engine(
        uri,
        use_insertmanyvalues=True,
        insertmanyvalues_page_size=10000,
    )


def _get_sessionmaker(uri: str):
    return sessionmaker(bind=_get_engine(uri))


def get_inspect_sessionmaker():
    uri = get_inspect_database_uri()
    return _get_sessionmaker(uri)


def get_inspect_session() -> orm.Session:
    session = get_inspect_sessionmaker()
    return session()


def create_tables():
    uri = get_inspect_database_uri()
    engine = _get_engine(uri)

    Base.metadata.bind = engine
    # if debug mode:
    # Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

# remove duplicate contracts:
# DELETE FROM contracts
# WHERE contract_address NOT IN (
#     SELECT MIN(contract_address)
#     FROM contracts
#     GROUP BY bytecode
# );
