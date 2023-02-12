# Inkserver
[<img src="https://img.shields.io/badge/dockerhub-valentinriess/inkserver-informational.svg?logo=DOCKER">](https://hub.docker.com/repository/docker/valentinriess/inkserver/tags)


This simple webserver can be used to provide adapted content for an Inkplate to fetch. It uses [ImageMagick](https://imagemagick.org/) to resize and transform the content.


My [Inkplate 10](https://inkplate.readthedocs.io/en/latest/index.html) uns a small script which
- connects to the Inkserver
- downloads the content
- displays the content on the eink screen
- goes into deep sleep until woken up again by timer

This server allows me to deliver dynamic content to the Inkplate without touching the code on the device itself.

Currently, two providers are implemented:
1. Local files: Randomly deliver a local file
2. XKCD: Randomly deliver a xkcd comic

![image](https://user-images.githubusercontent.com/8049779/218333425-add545a0-343a-4494-9c30-a128b76887ae.png)


## Setup
```
# Create auth_secret
echo "aSecureAuthSecret" > auth_secret

# Use docker compose to run server
docker compose up -d
```
