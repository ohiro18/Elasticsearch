FROM apache/incubator-superset:latest

RUN pip3 install --upgrade pip

# Install for pyodbc
RUN yum -y update
RUN yum -y install -y unixodbc-dev

ADD ./requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt


# Setup local admin account
RUN superset fab create-admin \
                 --username admin \
                 --firstname Superset \
                 --lastname Admin \
                 --email admin@superset.com \
                 --password admin

# Migrate local DB to latest
RUN superset db upgrade

# Load Examples
RUN superset load_examples

# Setup roles
RUN superset init

