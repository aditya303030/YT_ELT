from airflow import DAG
import pendulum
from datetime import datetime, timedelta
from api.video_stats import get_playList_id, get_video_ids, extract_video_data, save_to_json

from datawarehouse.dwh import staging_table, core_table

# define the local timezone
local_tz = pendulum.timezone("America/Chicago")

# Default Args
default_args = {
    "owner": "aditya3030",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "email": "data@engineers.com",
    # 'retries': 1,
    # 'retry_delay': timedelta(minutes=5),
    "max_active_runs": 1,
    "dagrun_timeout": timedelta(hours=1),
    "start_date": datetime(2025, 1, 1, tzinfo=local_tz),
    # 'end_date': datetime(2030, 12, 31, tzinfo=local_tz),
}

with DAG(
    dag_id = "produce_json",
    default_args=default_args,
    description="DAG to produce JSON file with raw data",
    schedule = "0 14 * * *",
    catchup=False
) as dag:
    
    # Define tasks
    playlist_id = get_playList_id()
    video_ids = get_video_ids(playlist_id)
    extracted_data = extract_video_data(video_ids)
    save_to_json_task = save_to_json(extracted_data)

    # Define dependencies (in the order of execution)
    playlist_id >> video_ids >> extracted_data >> save_to_json_task


with DAG(
    dag_id = "update_db",
    default_args=default_args,
    description="DAG to process JSON file and insert data into both staging and core schemas",
    schedule = "0 15 * * *",
    catchup=False
) as dag:
    
    # Define tasks
    update_staging = staging_table()
    update_core = core_table()
    
    # Define dependencies (in the order of execution)
    update_staging >> update_core
