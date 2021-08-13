#!/bin/bash
echo "Deploying new instance of Jupyterhub ..."

docker rm -f jhub &> /dev/null && \
  docker-compose up --remove-orphans --force-recreate --build -d $*

echo "Deploying is completed."

echo "Start synchronization ..."

source sync.sh
