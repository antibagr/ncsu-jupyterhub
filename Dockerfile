FROM jupyterhub/jupyterhub:latest

WORKDIR /srv/jupyterhub

# Install python dependencies

COPY ./requirements.txt requirements.txt

RUN python3 -m pip install --upgrade pip && python3 -m pip install -r requirements.txt --no-cache-dir

# Setup Nbgrader

RUN jupyter nbextension install --system --py nbgrader --overwrite \
  && jupyter nbextension enable --system --py nbgrader \
  && jupyter serverextension enable --system --py nbgrader

# Create exchange directory

RUN mkdir -p /srv/exchange && chmod ugo+rw /srv/exchange

# Update LTI authenticator with patched verion

COPY ltiauthenticator/__init__.py /usr/local/lib/python3.8/dist-packages/ltiauthenticator/__init__.py
