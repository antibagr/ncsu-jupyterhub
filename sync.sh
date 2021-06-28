echo "Starting synchronization ..."

docker exec -it jhub python3 lti_synchronization/app.py

echo "Restarting container ..."

docker restart jhub

docker logs jhub -f
