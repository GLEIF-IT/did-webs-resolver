#!/bin/bash
# aid-setup-and-doc-gen.sh
# Sets up the local AID for use by did:webs with one witness and then
# generates the DID document and KERI CESR stream for that AID.
#
# Note: this script requires it be run from the root did-webs-resolver directory

CWD="${PWD##*/}"
if [ "${CWD}" != "did-webs-resolver" ]; then
    echo "This script must be run from the root did-webs-resolver directory. It was run from the directory: ${CWD}"
    exit 1
fi

CONFIG_DIR="./local-config"
SCRIPTS_DIR="./local-scripts"
WEB_DIR="./local-web"
ARTIFACT_PATH="dws"

source "${SCRIPTS_DIR}"/color-printing.sh

# Binary Dependencies
command -v kli >/dev/null 2>&1 || { print_red "kli is not installed or not available on the PATH. Aborting."; exit 1; }
command -v dkr >/dev/null 2>&1 || { print_red "dkr is not installed or not available on the PATH. Aborting."; exit 1; }

# need to run witness network
DOMAIN=127.0.0.1
DID_PORT=7677
print_dark_gray "Assumes witnesses started and running..."
WAN_PRE=BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha
WIT_HOST=http://"${DOMAIN}":5642
WIT_OOBI="${WIT_HOST}/oobi/${WAN_PRE}"
curl $WIT_OOBI >/dev/null 2>&1
status=$?
if [ $status -ne 0 ]; then
    print_red "Witness server not running at ${WIT_HOST}"
    exit 1
else
    print_dark_gray "Witness server is running at ${WIT_OOBI}\n"
fi

# Set up identifying information for the controller AID and the did:webs DID
KEYSTORE_NAME="hyperledger"
AID_ALIAS="labs-id"
print_dark_gray "Creating controller AID ${KEYSTORE_NAME}/${AID_ALIAS} and did:webs for ${DOMAIN}"
# init environment for controller AID
exists=$(kli aid --name "${KEYSTORE_NAME}" --alias "${AID_ALIAS}" 2>/dev/null)
if [[ "${exists}" =~ ^E  || ! "${exists}" =~ Keystore* ]] ; then
  print_yellow "${KEYSTORE_NAME}/${AID_ALIAS} already exists, reusing ${exists}"
else
  print_dark_gray "does not exist, creating..."
  kli init \
    --name "${KEYSTORE_NAME}" \
    --salt 0AAFmiyF5LgNB3AT6ZkdN25B \
    --nopasscode \
    --config-dir "${CONFIG_DIR}" \
    --config-file "${KEYSTORE_NAME}"

  # inception for controller AID
  kli incept \
    --name "${KEYSTORE_NAME}" \
    --alias "${AID_ALIAS}" \
    --file "${CONFIG_DIR}/incept-with-wan-wit.json"
fi

MY_AID=$(kli aid --name "${KEYSTORE_NAME}" --alias "${AID_ALIAS}")
MY_OOBI="http://${DOMAIN}:5642/oobi/${MY_AID}/witness/${WAN_PRE}"

# check witness oobi for our AID
curl "${MY_OOBI}" >/dev/null 2>&1
status=$?
if [ $status -ne 0 ]; then
    print_red "Controller ${KEYSTORE_NAME}/${AID_ALIAS} with AID ${MY_AID} not found at ${MY_OOBI}"
    exit 1
else
    print_green "Controller ${KEYSTORE_NAME}/${AID_ALIAS} with AID ${MY_AID} setup complete."
fi

# generate controller did:webs for DOMAIN
MY_DID="did:webs:${DOMAIN}%3A${DID_PORT}:${ARTIFACT_PATH}:${MY_AID}"
print_dark_gray "Generating did:webs for ${KEYSTORE_NAME} on ${DOMAIN} with AID ${MY_AID} in ${WEB_DIR}"
print_lcyan "for DID ${MY_DID}"
dkr did webs generate \
  --name "${KEYSTORE_NAME}" \
  --output-dir "${WEB_DIR}" \
  --did "${MY_DID}"
