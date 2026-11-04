"""Construct internal URLs safely, including passwords with URL-special characters."""
import os
import sys
from sqlalchemy.engine import URL

if not os.getenv('DATABASE_URL'):
    os.environ['DATABASE_URL']=URL.create('postgresql+psycopg',username=os.environ['POSTGRES_USER'],password=os.environ['POSTGRES_PASSWORD'],host='postgres',port=5432,database=os.getenv('POSTGRES_DB','diabetes_mas')).render_as_string(hide_password=False)
if len(sys.argv)<2:
    raise SystemExit('A container command is required')
os.execvp(sys.argv[1],sys.argv[1:])
