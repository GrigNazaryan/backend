from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# pool_pre_ping avoids "server closed the connection unexpectedly" errors
# on cheap/free-tier Postgres instances that silently drop idle connections
# after a while — common on the kind of hosting a student project uses.
#
# client_encoding is forced to utf8 explicitly: on Windows, psycopg2 can
# default to the OS codepage (e.g. cp1251/cp866) instead of UTF-8 for the
# connection, which silently mangles non-Latin text (Armenian, Cyrillic)
# on the way into Postgres even when the database itself is UTF8.
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    connect_args={"client_encoding": "utf8"},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: yields a DB session, always closed after the
    request finishes, even if the request raised an exception."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()
