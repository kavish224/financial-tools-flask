# app/services/database.py
import psycopg2
import logging
from sqlalchemy.orm import scoped_session, sessionmaker, declarative_base
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# SQLAlchemy engine and session setup
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://Kavish:97642654875@localhost:5432/markets")
engine = create_engine(DATABASE_URL)
db_session = scoped_session(sessionmaker(autocommit=False, autoflush=False, bind=engine))
Base = declarative_base()

def init_db():
    """
    Initialize the database by creating tables if they don't exist.
    """
    try:
        import app.models  # Import all models here
        Base.metadata.create_all(bind=engine)
        logging.info("Database initialized successfully.")
    except Exception as e:
        logging.error(f"Error initializing the database: {str(e)}")
        raise

def get_db_session():
    """
    Return the SQLAlchemy scoped session.
    """
    return db_session

def get_db_connection():
    """
    Establish a direct connection to the database using psycopg2.
    """
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("DB_NAME", "markets"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "password"),
            host=os.getenv("DB_HOST", "localhost"),
            port=os.getenv("DB_PORT", "5432")
        )
        return conn
    except Exception as e:
        logging.error(f"Error connecting to database: {str(e)}")
        raise
