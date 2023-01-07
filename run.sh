#!/bin/bash

if [ -z "$(pgrep rootless)" ]
then
	echo -ne "Rootless Docker is a Happy Docker!"
	exit 1
fi

docker build -t owalert .
docker run -i --env-file=.env owalert
