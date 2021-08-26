echo "Starting synchronization ..."

# source sync.sh
# source sync.sh --path-out something.json

docker exec -it jhub python3 lti_synchronization/cli.py --path_in lti_synchronization/data/courses.json $*

echo "Restarting container ..."

docker restart jhub

docker logs jhub -f
