VERSION=0.2.1

define DOCKER_WARNING
In order to use the multi-platform build enable the containerd image store
The containerd image store is not enabled by default.
To enable the feature for Docker Desktop:
	Navigate to Settings in Docker Desktop.
	In the General tab, check Use containerd for pulling and storing images.
	Select Apply and Restart."
endef

build-dws-base: .warn
	@docker build \
		--platform=linux/amd64,linux/arm64 \
		-f images/dws-base.dockerfile \
		-t gleif/webs:$(VERSION) .

publish-dws-base:
	@docker push gleif/dws-base:$(VERSION)

tag-dws-base-latest:
	@$(MAKE) tag IMAGE_NAME=gleif/dws-base VERSION=$(VERSION)

tag-latest: tag-dws-base-latest tag-dws-web-service-latest tag-dws-resolver-latest

build-dws-web-service: .warn
	@docker build \
		--platform=linux/amd64,linux/arm64 \
		-f images/dws-webs-service.dockerfile \
		-t gleif/did-webs-service:latest \
		-t gleif/did-webs-service:$(VERSION) .

publish-dws-web-service:
	@docker push gleif/dws-web-service:$(VERSION)

tag-dws-web-service-latest:
	@$(MAKE) tag IMAGE_NAME=gleif/dws-web-service VERSION=$(VERSION)

build-did-webs-resolver: .warn
	@docker build \
		--platform=linux/amd64,linux/arm64 \
		-f images/did-webs-resolver.dockerfile \
		-t gleif/did-webs-resolver:latest \
		-t gleif/did-webs-resolver:$(VERSION) .

publish-did-webs-resolver:
	@docker push gleif/did-webs-resolver:$(VERSION)

tag-did-webs-resolver-latest:
	@$(MAKE) tag IMAGE_NAME=gleif/did-webs-resolver VERSION=$(VERSION)

run-agent:
	@docker run -p 5921:5921 -p 5923:5923 --name agent gleif/did-webs-resolver:$(VERSION)

publish-latest:
	@docker push gleif/dws-base:latest
	@docker push gleif/dws-web-service:latest
	@docker push gleif/did-webs-resolver:latest

.warn:
	@echo -e ${RED}"$$DOCKER_WARNING"${NO_COLOUR}

tag:
	@IMAGE_ID=$$(docker images --format "{{.ID}}" $(IMAGE_NAME):$(VERSION) | head -n 1); \
	if [ -z "$$IMAGE_ID" ]; then \
		echo "Error: No local image found for '$(IMAGE_NAME)'"; \
		exit 1; \
	fi; \
	docker tag $$IMAGE_ID $(IMAGE_NAME):latest; \
	echo "Successfully tagged $(IMAGE_NAME) ($$IMAGE_ID) as $(IMAGE_NAME):latest"

fmt:
	@uv tool run ruff check --select I --fix
	@uv tool run ruff format

# used by ci
check:
	uv tool run ruff check --select I
	uv tool run ruff format --check

RED="\033[0;31m"
NO_COLOUR="\033[0m"
export DOCKER_WARNING