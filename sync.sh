docker exec -it jhub python3 moodle_importer/app.py
docker restart jhub
docker logs jhub -f
