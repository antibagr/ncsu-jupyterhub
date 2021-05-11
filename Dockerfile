FROM jupyterhub/jupyterhub:latest

WORKDIR /srv/jupyterhub

# Install python dependencies

COPY ./requirements.txt requirements.txt

RUN python3 -m pip install --upgrade pip && python3 -m pip install -r requirements.txt --no-cache-dir

# Setup Nbgrader

RUN jupyter nbextension install --system --py nbgrader --overwrite \
  && jupyter nbextension enable --system --py nbgrader \
  && jupyter serverextension enable --system --py nbgrader

# Create exchange directory and directory for global nbgrader_config.py

RUN mkdir -p /srv/nbgrader/exchange && chmod ugo+rw /srv/nbgrader/exchange && \
    mkdir -p /etc/jupyter && chmod ugo+rw /etc/jupyter

# Update LTI authenticator with patched verion

COPY ltiauthenticator/__init__.py /usr/local/lib/python3.8/dist-packages/ltiauthenticator/__init__.py

# Update nbgrader to ignore SSL certificate.

COPY nbgrader/server_extensions/course_list/handlers.py /usr/local/lib/python3.8/dist-packages/nbgrader/server_extensions/course_list/handlers.py

# RUN apt-get update && apt-get install -y systemctl && apt-get install -y systemd

COPY global_nbgrader_config.py /etc/jupyter/nbgrader_config.py
