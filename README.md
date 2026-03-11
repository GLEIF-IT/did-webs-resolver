# did:webs resolver 

A DID resolver for did:webs and did:keri DIDs also compatible with the Universal Resolver.

A demonstration of a `did:webs` service and resolver. Implements the
`did:webs` [specification](https://trustoverip.github.io/kswg-did-method-webs-specification/).

[![CI](https://github.com/GLEIF-IT/did-webs-resolver/actions/workflows/ci.yml/badge.svg)](https://github.com/GLEIF-IT/did-webs-resolver/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/GLEIF-IT/did-webs-resolver/branch/main/graph/badge.svg?token=sUADtbanWC)](https://codecov.io/gh/GLEIF-IT/did-webs-resolver)

Components:
- **did:webs** static artifact generator - generates did.json and keri.cesr for did:webs DIDs.
- **did:webs** resolver in **static server mode** - serves static `did.json` and `keri.cesr` files from a local directory for did:webs DIDs. Works with the Universal Resolver subcomponent of the did:webs resolver below.
- **did:webs** dynamic artifact resolver - dynamically generates `did.json` and `keri.cesr` files upon receiving HTTP requests to `/{did path}/{aid}/{did.json,keri.cesr}`.
- **did:webs** resolver service - supports the DIF [Universal Resolver](https://dev.uniresolver.io/) at `/1.0/identifiers/{did}`
  - supports both **did:webs** and **did:keri** DID resolution. 

## Quick Start

The quick start shows you how to use either the Docker Compose setup or the local shell script setup to:
1. Generate did:webs artifacts (did.json, keri.cesr)
2. Host those artifacts using a static server
3. Resolve a did:webs DID against those artifacts using the `dws did webs resolve` command.
4. Resolve a did:keri DID against those artifacts using the `dws did keri resolve` command.
5. Run the `did:webs` resolver service in static server mode supporting the Universal Resolver.

### Docker

1. `docker compose up` - this will generate the did:webs assets (did.json, keri.cesr), start the static server, start the `did:webs` resolver service, and boot up the `dws-shell` container.
2. `docker compose exec -it dws-shell /bin/bash` - drop in to the shell container to run commands.
3. review the `./docker/test-resolutions.sh` for a guide on how to use either the universal resolver resource or the `dws did webs resolve` command to resolve did:webs DIDs.

### Local Shell Script

1. `kli witness demo` to start the witnesses up. Run this from the root of the `keripy` respository in a separate terminal window.
2. Create a local Python virtual environment with `uv lock` and `uv sync` to install the dependencies.
3. Source the uv environment with `source .venv/bin/activate`.
4. Run the local script with `./local/did_webs_workflow.sh` to view the end-to-end resolution process.

## Developers - Getting Started

Developers who want to jump into using the `did:webs` reference implementation should follow
the [Getting Started](docs/getting_started.md) guide.

A breakdown of the commands can be found [here](./docs/commands.md).

#### did:webs service

For a `did:webs` service to operate securely it should only serve AIDs whose KELs have been processed into the service's database.

There are two methods to do this:

1. Local only support - start the service using an existing local keystore.

This is useful for development and can be done by provide an existing named keystore to the `did:webs` service.

For example, to start the service using the `multisig1` keystore (https://github.com/WebOfTrust/keripy/blob/v1.2.4/scripts/demo/basic/multisig.sh)

```bash
dws did webs service --name multisig1
```

2. Import supported - start the service using an empty local keystore, and import AID KELs. The following workflow can be applied to start the service, export an existing keystore and import it to the service.

```bash
dws did webs service --name dws
```

```bash
kli export --name multisig1 --files 
```

to import an AID to the service securely we use a IPEX Grant to present the exported KEL to the service.

```bash
kli grant 
```


#### Bootstrapping

### Prior art

did:keri resolver by Philip Feairheller @pfeairheller [here](https://github.com/WebOfTrust/did-keri-resolver)

Thank you to Markus Sabadello @peacekeeper from DanubeTech who started the original tutorial for
IIW37 [here](https://github.com/peacekeeper/did-webs-iiw-tutorial)

# Development Warnings

- Some of the tests in test_habs.py and test_clienting.py are flaky, so re-running the tests is fine. We need to use more mocks there. The problem in habbing gets down to how the "temp=False" option causes Filer to use or not use temporary filesystem files. We should just mock this out. The problem in clienter is likely due to timeouts not being set with enough of a margin of error. Mocking here might be the best solution as well. 
