echo "Starting synchronization ..."

docker exec -it jhub python3 lti_synchronization/sync.py

echo "Restarting container ..."

docker restart jhub

docker logs jhub -f
