#!/bin/bash

echo "start deploying"

echo "[1/2] stop old app"
sudo docker-compose down

echo "[2/2] deploy new app"
sudo docker-compose build
sudo docker-compose up -d

echo "[3/3] remove dangling images"
printf "y" | sudo docker image prune
