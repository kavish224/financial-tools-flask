# config.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPSTOX_HIST_API_URL = 'https://api.upstox.com/v2/historical-candle/'


class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

    

# class DevelopmentConfig(Config):
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
#     SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')

# class ProductionConfig(Config):
#     SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')