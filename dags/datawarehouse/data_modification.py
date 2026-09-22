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
                    %(commentCount)s,
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
                    "Video_type",
                    "Video_Views",
                    "Likes_Count",
                    "Comments_Count"
                )
                VALUES (
                    %(video_id)s,
                    %(title)s,
                    %(publishedAt)s,
                    %(duration)s,
                    %(Video_Type)s,
                    %(viewCount)s,
                    %(likeCount)s,
                    %(commentCount)s
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
            # Map the raw API field names used by a staging row.
            video_id = "video_id"
            video_title = "title"
            upload_date = "publishedAt"
            duration = "duration"
            video_views = "viewCount"
            likes_count = "likeCount"
            comments_count = "commentCount"
        
        else:
            # Map the warehouse field names used by a core row.
            video_id = "Video_ID"
            video_title = "Video_Title"
            upload_date = "Upload_Date"
            video_views = "Video_Views"
            likes_count = "Likes_Count"
            comments_count = "Comments_Count"

        # Match the existing record by its video ID and upload date, then
        # overwrite only attributes that can change between API extracts.
        cursor.execute(
            f"""
                UPDATE {schema}.{table}
                SET "Video_Title" = %(video_title)s,
                    "Video_Views" = %(video_views)s,
                    "Likes_Count" = %(likes_count)s,
                    "Comments_Count" = %(comments_count)s
                WHERE "Video_ID" == %(video_id)s AND "Upload_Date" == %(upload_date)s
            """, row
        )
    
        # Persist the update before logging a successful result.
        conn.commit()
        logger.info(f"Updated row with Video_ID: {row[video_id]}")

    except Exception as e:
        # Record the failure for diagnosis. This function currently logs the
        # exception but does not re-raise it.
        logger.error(f"Error updating file with Video_ID: {row[video_id]}")


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
