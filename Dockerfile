FROM jupyterhub/jupyterhub:latest

# All files related to Jupyterhub instance will be placed
# in /srv/jupyterhub

WORKDIR /srv/jupyterhub


# Update package list in order
# To install several Ubuntu utils.

RUN apt-get update && apt-get install git nano bash sudo -yq && rm -rf /var/lib/apt/lists/*


# Install python dependencies

COPY requirements.prod.txt requirements.txt

RUN python3 -m pip install --upgrade pip \
  && python3 -m pip install -r requirements.txt --no-cache-dir


# Install nbgrader system-wide
# Enable only assignment_list by default for any user.

RUN jupyter nbextension install --system --py nbgrader --overwrite \
  && jupyter nbextension enable --sys-prefix assignment_list/main --section=tree \
  && jupyter serverextension enable --sys-prefix nbgrader.server_extensions.assignment_list


# Create exchange directory with appropriate permissions
# Create directory for global nbgrader_config.py

RUN mkdir -p /srv/nbgrader/exchange && \
    chmod ugo+rw /srv/nbgrader/exchange && \
    mkdir -p /etc/jupyter && \
    chmod ugo+rw /etc/jupyter


# Copy default jupyterhub configuration

COPY lti_synchronization/default_jupyterhub_config.py jupyterhub_config.py

COPY lti_synchronization/ .

RUN python3 lti_synchronization/setup.py install

COPY lti_synchronization /usr/local/lib/python3.8/dist-packages/lti_synchronization
