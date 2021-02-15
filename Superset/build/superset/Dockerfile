FROM apache/incubator-superset:latest

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

