FROM jupyterhub/jupyterhub:latest

WORKDIR /srv/jupyterhub

# Install python dependencies

COPY requirements.txt .

RUN python3 -m pip install --upgrade pip && python3 -m pip install -r requirements.txt --no-cache-dir

# Setup Nbgrader

RUN jupyter nbextension install --system --py nbgrader --overwrite \
  && jupyter nbextension enable --system --py nbgrader \
  && jupyter serverextension enable --system --py nbgrader

# Create exchange directory and directory for global nbgrader_config.py

RUN mkdir -p /srv/nbgrader/exchange && \
    chmod ugo+rw /srv/nbgrader/exchange && \
    mkdir -p /etc/jupyter && \
    chmod ugo+rw /etc/jupyter

# COPY ./jupyterhub_config.py .

RUN apt-get update && apt-get install nano

COPY jupyterhub_config.py .
