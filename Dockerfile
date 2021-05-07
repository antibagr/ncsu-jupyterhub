FROM jupyterhub/jupyterhub:latest

WORKDIR /srv/jupyterhub

# Install python dependencies

RUN python3 -m pip install -r requirements.txt

# Setup Nbgrader

RUN jupyter nbextension install --system --py nbgrader --overwrite \
  && jupyter nbextension enable --system --py nbgrader \
  && jupyter serverextension enable --system --py nbgrader

# Create exchange directory

RUN mkdir -p /srv/exchange && chmod ugo+rw /srv/exchange
