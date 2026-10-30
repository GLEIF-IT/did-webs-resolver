# Changelog for did:webs resolver

## Version History

### 0.3.8 Use the GLEIF KERI 1.2.18 security release

Upgrade to `gleif_keri==1.2.18` and `gleif_hio==0.6.22`, carrying the
delegated-rotation replay correction, current Python dependency security floors,
and maintained HTTP connection cleanup into the resolver. Build the service
images from the matching immutable KERI base and version the dependent images
together.

### 0.3.7 Upgrade KERIpy to 1.2.13

There was an important LMDB bugfix in KERIpy 1.2.13 that we pull in here.

### 0.3.6 Pinned Designated Aliases Schema

Make did-webs-resolver usage painless and turnkey by pinning the designated aliases ACDC schema
so users of the did:webs resolver do not have to have their AID resolve the designated aliases
ACDC schema OOBI prior to being able to successfully resolve a `did:webs` DID.

This really simplifies did-webs-resolver usage as it removes a step everyone using it would have
to do. And this is easy to forget during development, so it saves a bunch of dev time.

### 0.3.5 Remove unneeded vgate dependency

The vgate dependency was never used so removing it simplifies things.

### 0.3.4 Upgrade to KERIpy 1.2.12 and test fixes

Just a few test fixes to get test coverage back to 100%, a quoting fix on re-encoding invalid did:webs DIDs, and upgrade to KERIpy 1.2.12, the latest release.

### 0.3.2 Delegation and alsoKnownAs features

- Added support for delegator blocks in `service` section.
- Added default `did:keri` and `did:web` alsoKnownAs entries in DID doc generation.

### 0.3.1 repackage from dkr -> dws

- fix HTTP stream consumption in logger middleware
- add some test fixtures for ACDC schemas


### 0.3.0 First release under GLEIF-IT/did-webs-resolver

- Changed root package name to `dws` from `dkr` to reflect semantic name of did:webs.
- Fixed broken constant imports, added missing constants.
- Upgraded to KERI 1.2x.
- Added `version` command.
- Fixed logging and used TruncatedFormatter.
- Refactored to use small functions all around for readability and testability.
- Added unit and integration tests. 
- Added output dir for DID artifacts instead of just default output dir.
- Added sample script for local DID doc generation.
- Fixed static file hosting and resolution to default to HTTPS and fall back to HTTP.
- `--loglevel` arg added to CLI.
- Idiomatic Hio usage for DoDoers
- Corrected the `meta` field usage throughout the resolver.
- `--verbose` argument added to CLI for more detailed output.
- Fixed HTTP port conversion.
- Removed all shelling out and replaced it with using the appropriate Doers for did:webs resolution.
- Added code formatting.
- Cleaned up the getting started docs.
- Fixed the designated alias ACDC processing.
- Removed the `--regname` argument in favor of scanning all local ACDC registries for self-attested designated alias ACDCs.
- Added a complete end-to-end workflow script.
- Added a health check endpoint to the did:webs resolver server.
- Got rid of old, unused scripts and config.
- Add support for path segments to the core.ends endpoints.
- Add did_path for specifying where to host DID assets.
- Fix HIO's urllib.parse of path in environ PATH_INFO.
- Add integration style resolution tests and witness integration tests.
- Make did:keri resolution work with OOBI resolution.
- Get test coverage to 100%
- Fix the docker compose setup to work with local test did:webs resolutions.
- `X-Forwarded-Port` for supporting resolver deployments behind HTTP proxies.
- Fix Location Scheme record save bug.

## Versions prior to 0.3.0 (hyperledger-labs/did-webs-resolver history)

#### 0.0.7 and before

Initial draft. 
- Partial implementation of did:webs resolver.
- did:keri resolver imported from https://github.com/WebOfTrust/did-keri-resolver
