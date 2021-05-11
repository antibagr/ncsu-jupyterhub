rm -rf backup/*

docker exec -it jhub sh backup.sh

backup_file=backup/$(ls backup)

sshpass -p $REMOTE_PASSWORD scp $backup_file root@185.237.96.248:/root/ncsu-jupyterhub/uploaded/

rm -rf backup/*
