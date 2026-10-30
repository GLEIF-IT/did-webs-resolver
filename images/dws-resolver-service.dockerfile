FROM gleif/dws-base:0.3.8
# This image runs the did:webs and did:keri resolver. The local controller AID does not matter
# very much as it is only used to run the local keystore, not to sign anything.
# the "dws" keystore can be replaced with any other name, yet it should match the name of the
# config file at /dws/config/<config_file_name>.json if you want it to pick up the config there.

EXPOSE 7677

WORKDIR /dws

# Bootstrap keystore (Habery) configuration file.
COPY images/dws.json /dws/config/keri/cf/dws.json

# Set up the local keystore to know about the designated alias public schema
# so it can parse and receive designated aliases ACDCs to populate alsoKnownAs and equivalentIds
# sections of the did:webs DID documents.

RUN kli init \
  --name "dws" \
  --config-dir /dws/config \
  --config-file dws.json \
  --nopasscode

RUN kli oobi resolve \
  --name "dws" \
  --oobi-alias "designated-alias-public-schema" \
  --oobi "https://weboftrust.github.io/oobi/EN6Oh5XSD5_q2Hgu-aqpdfbVepdpYpFlgz6zvJL5b_r5"

# Default resolver run command
CMD ["dws", "did", "webs", "resolver-service", \
    "--name", "dws", \
    "--config-dir", "/dws/config", \
    "--config-file", "dws.json", \
    "--http", "7677", \
    "--loglevel", "INFO" \
    ]
