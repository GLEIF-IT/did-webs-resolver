FROM gleif/dws-base:0.3.8
# This image runs the did:webs and did:keri dynamic asset generator and webserver of did.json and keri.cesr files.
# The local controller AID matters because it is used to generate the did.json and keri.cesr files.

EXPOSE 7678

WORKDIR /dws

# A default command is not included since the local KERI controller AID used should be specific to
# your deployment and the keystore name should match the name of your keystore.
# The command below is included for reference.
# It would dynamically generate and respond with did assets for the following sample did:webs DID:
#   did:webs:127.0.0.1%3A7678:dws:EBFn5ge82EQwxp9eeje-UMEXF-v-3dlfbdVMX_PNjSft
# Notice the `--did-path` argument is set to `dws` which matches the path component in the sample DID.
CMD ["dws", "did", "webs", "service", "-p", "7678", "--name", "my-controller", "--config-dir", "/dws/config", "--config-file", "my-controller.json", "--alias", "my-aid-alias", "--did-path", "dws", "--loglevel", "INFO" ]
