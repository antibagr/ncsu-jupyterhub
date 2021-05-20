docker rm -f jhub &> /dev/null && \
  docker-compose up --remove-orphans --force-recreate --build -d $* && \
  sleep 1 && \
  docker logs jhub -f
