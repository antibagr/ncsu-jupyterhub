FROM jupyterhub/jupyterhub:latest

WORKDIR /srv/jupyterhub

# Install python dependencies

COPY requirements.txt .

RUN python3 -m pip install --upgrade pip && python3 -m pip install -r requirements.txt --no-cache-dir

# Setup Nbgrader

RUN jupyter nbextension install --system --py nbgrader --overwrite \
  && jupyter nbextension enable --sys-prefix assignment_list/main --section=tree \
  && jupyter serverextension enable --sys-prefix nbgrader.server_extensions.assignment_list


# Create exchange directory and directory for global nbgrader_config.py

RUN mkdir -p /srv/nbgrader/exchange && \
    chmod ugo+rw /srv/nbgrader/exchange && \
    mkdir -p /etc/jupyter && \
    chmod ugo+rw /etc/jupyter

# Update package list and install nano and bash

RUN apt-get update && apt-get install nano bash sudo -yq && rm -rf /var/lib/apt/lists/*

COPY jupyterhub_config.py .
