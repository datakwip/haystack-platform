aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin 032363835097.dkr.ecr.us-east-1.amazonaws.com
docker build --no-cache -t db-service-layer .
docker tag db-service-layer:latest 032363835097.dkr.ecr.us-east-1.amazonaws.com/db-service-layer:1.73
docker push 032363835097.dkr.ecr.us-east-1.amazonaws.com/db-service-layer:1.73