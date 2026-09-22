import logging


# Use Airflow/Python logging so insert, update, and delete outcomes are
# available in the task logs.
logger = logging.getLogger(__name__)

# Both the staging and core schemas use the same table name.
table = "yt_api"

# Inserts one video dictionary into either the staging or core version of the
# table. `row` supplies the named values used by psycopg2's %(name)s placeholders.
def insert_rows(cursor, conn, schema, row):
    try:
        if schema == "staging":
            # Raw API rows use lowercase/camelCase dictionary keys.
            video_id = "video_id"

            # The schema/table name is inserted into the SQL string, while row
            # values remain parameterized to safely bind the data values.
            cursor.execute(
                f"""INSERT INTO {schema}.{table} (
                    "Video_ID",
                    "Video_Title",
                    "Upload_Date",
                    "Duration",
                    "Video_Views",
                    "Likes_Count",
                    "Comments_Count"
                )
                VALUES (
                    %(video_id)s,
                    %(title)s,
                    %(publishedAt)s,
                    %(duration)s,
                    %(viewCount)s,
                    %(likeCount)s,
                    %(commentCount)s
                )
                """, row
            )
        else:
            # Core rows use the warehouse-style column names as dictionary keys.
            video_id = "Video_ID"
            cursor.execute(
                f"""INSERT INTO {schema}.{table} (
                    "Video_ID",
                    "Video_Title",
                    "Upload_Date",
                    "Duration",
                    "Video_Type",
                    "Video_Views",
                    "Likes_Count",
                    "Comments_Count"
                )
                VALUES (
                    %(Video_ID)s,
                    %(Video_Title)s,
                    %(Upload_Date)s,
                    %(Duration)s,
                    %(Video_Type)s,
                    %(Video_Views)s,
                    %(Likes_Count)s,
                    %(Comments_Count)s
                )
                """, row
            )
        
        # Make the successful INSERT permanent before reporting it as complete.
        conn.commit()

        logger.info(f"Inserted row with Video_ID: {row[video_id]}")

    except Exception as e:
        # Include the ID in the task log, then re-raise so Airflow marks the
        # calling task as failed instead of silently continuing.
        logger.error(f"Error inserting row with Video_ID: {row[video_id]}")
        raise e
    

# Updates the mutable video attributes of one existing database row.
def update_rows(cursor, conn, schema, row):
    try:
        if schema == "staging":
            # A staging row comes directly from the JSON file, so its keys use
            # the original YouTube API names (for example, `title`).
            video_id = "video_id"
            update_sql = f"""
                UPDATE {schema}.{table}
                SET "Video_Title" = %(title)s,
                    "Video_Views" = %(viewCount)s,
                    "Likes_Count" = %(likeCount)s,
                    "Comments_Count" = %(commentCount)s
                WHERE "Video_ID" = %(video_id)s
                  AND "Upload_Date" = %(publishedAt)s
            """
        
        else:
            # A core row was fetched from PostgreSQL, so its dictionary keys
            # match the quoted database column names.
            video_id = "Video_ID"
            update_sql = f"""
                UPDATE {schema}.{table}
                SET "Video_Title" = %(Video_Title)s,
                    "Video_Views" = %(Video_Views)s,
                    "Likes_Count" = %(Likes_Count)s,
                    "Comments_Count" = %(Comments_Count)s
                WHERE "Video_ID" = %(Video_ID)s
                  AND "Upload_Date" = %(Upload_Date)s
            """

        # Bind the row dictionary to the SQL placeholders and update only the
        # mutable values for the matching video record.
        cursor.execute(update_sql, row)
    
        # Persist the update before logging a successful result.
        conn.commit()
        logger.info(f"Updated row with Video_ID: {row[video_id]}")

    except Exception as e:
        # Include the original database error and re-raise it so Airflow marks
        # the task as failed instead of reporting a false success.
        logger.error(f"Error updating row with Video_ID {row[video_id]}: {e}")
        raise


# Deletes all rows whose video IDs are included in `ids_to_delete`.
def delete_rows(cursor, conn, schema, ids_to_delete):

    try:
        # Convert a Python collection such as ["a", "b"] into the SQL text
        # ('a', 'b'), which is used by the IN clause below.
        ids_to_delete = f""" ({', '.join(f"'{id}'" for id in ids_to_delete)}) """

        # Run one DELETE statement for the complete set of stale video IDs.
        cursor.execute(
            f"""
                DELETE FROM {schema}.{table}
                where "Video_ID" in {ids_to_delete}
            """
        )

        # Make the deletion permanent only after the SQL statement succeeds.
        conn.commit()
        logger.info(f"Successfully delete rows with Video_IDs: {ids_to_delete}")
    
    except Exception as e:
        # Re-raise after logging so an Airflow task cannot report a false success.
        logger.error(f"Error deleting rows with Video_IDs: {ids_to_delete} - {e}")
        raise e
