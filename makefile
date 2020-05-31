IMG_NAME=tnt_test

COMMAND_RUN=docker run \
	  --name {IMG_NAME} \
	  --detach=false \
	  --rm \
	  -v `pwd`:/usr/src/myapp \
	  -i \
	  -t \
	  ${IMG_NAME} /bin/bash -c

build:
	docker build --network host --no-cache --rm -t ${IMG_NAME} .

remove-image:
	docker rmi ${IMG_NAME}

run:
	$(COMMAND_RUN) \
            "cd /usr/src/myapp && bash"