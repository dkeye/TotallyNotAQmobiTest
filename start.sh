docker build --no-cache -t mytestimage .
docker run -d --name mytestimagecontainer -p 8080:8080 mytestimage
echo "ctrl+d to exit"
cat
docker stop mytestimagecontainer
# shellcheck disable=SC2046
docker rm $(docker ps -a -f name=mytestimagecontainer -q)
docker image rm mytestimage
