cwd=$(pwd)

mute=/dev/null

echo Clean up backup folder

rm -rf $cwd/backup/* > $mute

# Tar /home folder in the Docker to /backup folder in container

echo Running backup.sh in Docker

docker exec -it jhub sh backup.sh > $mute

echo New backup created: $(ls $cwd/backup/)

# Take filename from mounted backup folder

backup_file=$cwd/backup/$(ls $cwd/backup/)

# Move it to a remote server

echo Transfer backup file to remote server

# Installing sshpass if not installed

(which sshpass || apt-get install sshpass) > $mute

# In case you receive 'host key verification failed' error
# You need to connect to remote host without sshpass and add it allowed hosts.

if [[ -z "${REMOTE_PASSWORD}" ]]; then
	echo "$REMOTE_PASSWORD is not set. Please set this environment variable to transfer the backup file."
	return
fi

sshpass -p $REMOTE_PASSWORD scp $backup_file root@185.237.96.248:/root/ncsu-jupyterhub/uploaded/ # || echo Error: Failed to transfer backup file to remote server

echo Transferring completed. Clean up backup/ folder.

rm -rf $cwd/backup/*
