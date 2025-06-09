import os
RESET_PASS_LINK="http://risk.pragmadigital.in/reset-password?token="

class Config:
    SECRET_KEY='PragmaticSecret@2024'
    SQLALCHEMY_DATABASE_URI = "postgresql://postgres:Pragmatic$2004@risk-database.cvsou8myklaa.ap-south-1.rds.amazonaws.com:5432/risk_profiles"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    RESET_PASS_LINK="http://risk.pragmadigital.in/reset-password?token="
   

