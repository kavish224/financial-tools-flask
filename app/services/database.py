import psycopg2
import logging
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from contextlib import contextmanager

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logger.error("DATABASE_URL environment variable not set.")
    raise ValueError("DATABASE_URL environment variable not set.")

engine = create_engine(
    DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600
)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
def get_db_session():
    """
    Return the SQLAlchemy scoped session.
    """
    return db_session
@contextmanager
def get_db_connection():
    """
    Establish a direct connection to the database using psycopg2.
    """
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT")
        )
        yield conn
    except Exception as e:
        logging.error(f"Error connecting to database: {str(e)}")
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()
