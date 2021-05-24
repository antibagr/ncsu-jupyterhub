docker rm -f jhub &> /dev/null && \
  docker-compose up --remove-orphans --force-recreate --build -d $* && \
  sleep 1 && \
#  docker exec -it jhub python3 moodle_importer/app.py
  docker logs jhub -f
