import os
import psycopg2 as ps
from psycopg2 import sql


def postgresConnect():
    '''
    DESCRIPTION:
        Create connection to AWS RDS postgres DB and cursor
    '''
    conn = ps.connect(host=os.environ.get('AWS_POSTGRES_ADDRESS'),
                      database=os.environ.get('AWS_POSTGRES_DBNAME'),
                      user=os.environ.get('AWS_POSTGRES_USERNAME'),
                      password=os.environ.get('AWS_POSTGRES_PASSWORD'),
                      port=os.environ.get('AWS_POSTGRES_PORT'))
    return conn.cursor()


def exact_recipe_match(search_term, cur):
    '''
    DESCRIPTION:
        Return True if search_term is in recipes table of
        cur database, False otherwise.
    '''
    cur.execute(sql.SQL("""
                        SELECT * FROM public.recipes
                        WHERE "url" = %s
                        """).format(), [search_term]
                )
    if cur.fetchall():
        print(True)
    else:
        print(False)