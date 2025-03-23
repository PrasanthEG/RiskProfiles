import os

class Config:
    SECRET_KEY='PragmaticSecret@2024'
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:postgres123@localhost:5432/risk_profile"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
   

