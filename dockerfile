ARG AIRFLOW_VERSION=2.9.2
ARG PYTHON_VERSION=3.10

FROM apache/airflow:${AIRFLOW_VERSION}-python${PYTHON_VERSION}

# specify home environment variable - directory that contains important airflow folders like the DAGs and logs folders and airlfow config file
ENV AIRFLOW_HOME=/opt/airflow

# command used to copy the requirements.txt file from local directory to root directory
COPY requirements.txt /

# no-cache-fir option ensures that pip does not catch the packages, which helps in keeping the image size smaller
RUN pip install --no-cache-dir "apache-airflow==${AIRFLOW_VERSION}" -r /requirements.txt