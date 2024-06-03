import os

SECRET_KEY = 'secret-key'

# SQLALCHEMY_DATABASE_URI = 'sqlite:///project.db'
SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://std_2497_lab6:314159265@std-mysql.ist.mospolytech.ru/std_2497_lab6'
SQLALCHEMY_TRACK_MODIFICATIONS = False
SQLALCHEMY_ECHO = True

UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'media', 'images')
