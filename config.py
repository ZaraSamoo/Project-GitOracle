import os

class Config:
    # Use the Git_Oracle DB we set up earlier
    SQLALCHEMY_DATABASE_URI = 'postgresql://postgres:zed14axe@127.0.0.1:5432/Git_Oracle'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'giki-secret-key' # You can change this later