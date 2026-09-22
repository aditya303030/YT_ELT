from airflow.providers.postgres.hooks.postgres import PostgresHook
from psycopg2.extras import ReadDictCursor

table = "yt_api"

# Opens a PostgreSQL connection and returns it with a dictionary-style cursor.
def get_conn_cursor():
    hook = PostgresHook(postgres_conn_id="postgres_db_yt_elt", database="elt_db")
    conn = hook.get_conn()
    cursor = conn.cursor(cursor_factory=ReadDictCursor) # realdictcursor changes how the data is returned when we execute a query
    return conn, cursor
    

# Closes the provided PostgreSQL cursor and its associated connection.
def close_conn_cursor(conn, cursor):
    cursor.close()
    conn.close

# Creates the named PostgreSQL schema when it does not already exist.
def create_schema(schema):

    conn, cursor = get_conn_cursor()
    
    schema_sql = f"CREATE SCHEMA IF NOT EXISTS {schema};"

    cursor.execute(schema_sql)

    conn.commit()

    close_conn_cursor(conn, cursor)

# Creates a staging or warehouse video table with the schema-specific columns.
def create_table(schema):
    conn, cursor = get_conn_cursor()

    if schema == "staging":
        table_sql = f"""
                CREATE TABLE IF NOT EXISTS {schema}.{table} (
                    "Video_ID" VARCHAR(11) PRIMARY KEY NOT NULL,
                    "Video_Title" TEXT NOT NULL,
                    "Upload_Date" TIMESTAMP NOT NULL,
                    "Duration" VARCHAR(20) NOT NULL,
                    "Video_Views" INT,
                    "Likes_Count" INT,
                    "Comments_Count" INT
                );
               """
    else:
        table_sql = f"""

                CREATE TABLE IF NOT EXISTS {schema}.{table} (
                    "Video_ID" VARCHAR(11) PRIMARY KEY NOT NULL,
                    "Video_Title" TEXT NOT NULL,
                    "Upload_Date" TIMESTAMP NOT NULL,
                    "Duration" VARCHAR(20) NOT NULL,
                    "Video_Type" VARCHAR(10) NOT NULL,
                    "Video_Views" INT,
                    "Likes_Count" INT,
                    "Comments_Count" INT
                );        
                """
    cursor.execute(table_sql)

    conn.commit()

    close_conn_cursor(conn, cursor)


# Returns all existing video IDs from the specified schema's video table.
def get_video_ids(cursor, schema):
    
    cursor.execute(f"""SELECT "Video_ID" FROM {schema}.{table};""")
    # this will give a list of dictionaries where the key is the variable name and the value is the value of the variable Video_ID
    ids = cursor.fetchall() 

    video_ids = [id.get("Video_ID") for id in ids]

    return video_ids
