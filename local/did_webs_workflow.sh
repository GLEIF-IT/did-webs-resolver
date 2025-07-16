#!/bin/bash
# did_webs_workflow.sh
# Sets up the local AID for use by did:webs with one witness and then
# generates the DID document and KERI CESR stream for that AID.
#
# Note: this script requires it be run from the root did-webs-resolver directory
#   - `kli witness demo` should be running in another terminal.
CONFIG_DIR="./local/config"
SCRIPTS_DIR="./local"
WEB_DIR="./local/web"
ARTIFACT_PATH="dws"
source "${SCRIPTS_DIR}"/color-printing.sh

METADATA_TRUE=$1
print_yellow "METADATA_TRUE: ${METADATA_TRUE}"

CWD="${PWD##*/}"
if [ "${CWD}" != "did-webs-resolver" ]; then
    echo "This script must be run from the root did-webs-resolver directory. It was run from the directory: ${CWD}"
    exit 1
fi

# Binary Dependencies
command -v kli >/dev/null 2>&1 || { print_red "kli is not installed or not available on the PATH. Aborting."; exit 1; }
command -v dkr >/dev/null 2>&1 || { print_red "dkr is not installed or not available on the PATH. Aborting."; exit 1; }

# need to run witness network
DOMAIN=127.0.0.1
DID_PORT=7677
print_dark_gray "Assumes witnesses started and running..."
WAN_PRE=BBilc4-L3tFUnfM_wJr4S4OJanAv_VmF_dJNN6vkf2Ha

function check_witnesses() {
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
}
check_witnesses

# Set up identifying information for the controller AID and the did:webs DID
KEYSTORE_NAME="hyperledger"
AID_ALIAS="labs-id"
DESG_ALIASES_REG="did:webs_designated_aliases"
DESG_ALIASES_SCHEMA="EN6Oh5XSD5_q2Hgu-aqpdfbVepdpYpFlgz6zvJL5b_r5"
print_dark_gray "Creating controller AID ${KEYSTORE_NAME}/${AID_ALIAS} and did:webs for ${DOMAIN}"
# init environment for controller AID
function create_aid() {
  # Create keystore, AID, verify witness accessibility, and resolve the designated aliases schema
  kli init --name "${KEYSTORE_NAME}" --salt 0AAFmiyF5LgNB3AT6ZkdN25B --nopasscode --config-dir "${CONFIG_DIR}/controller" --config-file "${KEYSTORE_NAME}"
  # inception for controller AID
  kli incept --name "${KEYSTORE_NAME}" --alias "${AID_ALIAS}" --file "${CONFIG_DIR}/controller/incept-with-wan-wit.json"

  # check witness oobi for our AID
  MY_OOBI="http://${DOMAIN}:5642/oobi/${MY_AID}/witness/${WAN_PRE}"
  curl "${MY_OOBI}" >/dev/null 2>&1
  status=$?
  if [ $status -ne 0 ]; then
      print_red "Controller ${KEYSTORE_NAME}/${AID_ALIAS} with AID ${MY_AID} not found at ${MY_OOBI}"
      exit 1
  else
      print_green "Controller ${KEYSTORE_NAME}/${AID_ALIAS} with AID ${MY_AID} setup complete."
  fi
}

function set_up_aid() {
  exists=$(kli aid --name "${KEYSTORE_NAME}" --alias "${AID_ALIAS}" 2>/dev/null)
  if [[ "${exists}" =~ ^E  || ! "${exists}" =~ Keystore* ]] ; then
    print_dark_gray "${KEYSTORE_NAME}/${AID_ALIAS} already exists, reusing ${exists}"
  else
    print_dark_gray "does not exist, creating..."
    create_aid
    kli oobi resolve --name "${KEYSTORE_NAME}" \
    --oobi-alias "designated-alias-public" \
    --oobi "https://weboftrust.github.io/oobi/${DESG_ALIASES_SCHEMA}"
  fi
}
set_up_aid

MY_AID=$(kli aid --name "${KEYSTORE_NAME}" --alias "${AID_ALIAS}")
DESIG_ALIASES_FILE="${SCRIPTS_DIR}/designated_aliases.json"

function create_designated_aliases_json() {
  timestamp=$(kli time | tr -d '[:space:]')
    read -r -d '' DESIG_ALIASES_JSON << EOM
{
  "d": "",
  "dt": "${timestamp}",
  "ids": [
    "did:web:${DOMAIN}%3a${DID_PORT}:${MY_AID}",
    "did:webs:${DOMAIN}%3a${DID_PORT}:${MY_AID}",
    "did:web:example.com:${MY_AID}",
    "did:web:foo.com:${MY_AID}",
    "did:webs:foo.com:${MY_AID}"
  ]
}
EOM
    print_lcyan "building designated aliases JSON: ${DESIG_ALIASES_FILE}"
    echo "$DESIG_ALIASES_JSON" > "${DESIG_ALIASES_FILE}"
    kli saidify --file "${DESIG_ALIASES_FILE}"
    ALIASES=$(< "${DESIG_ALIASES_FILE}" jq)
    print_lcyan "${ALIASES}"
}

function create_desg_aliases_registry() {
  kli vc registry incept \
    --name "${KEYSTORE_NAME}" \
    --alias "${AID_ALIAS}" \
    --registry-name "${DESG_ALIASES_REG}"
  print_green "Created designated aliases registry ${KEYSTORE_NAME}/${AID_ALIAS} with AID ${MY_AID}"
}

function create_desg_aliases_cred() {
  kli vc create \
    --name "${KEYSTORE_NAME}" \
    --alias "${AID_ALIAS}" \
    --registry-name "${DESG_ALIASES_REG}" \
    --schema "${DESG_ALIASES_SCHEMA}" \
    --data @"${DESIG_ALIASES_FILE}" \
    --rules @"${SCRIPTS_DIR}/schema/rules/desig-aliases-public-schema-rules.json"
  print_green "Created designated aliases credential for ${KEYSTORE_NAME}/${AID_ALIAS} with AID ${MY_AID}"
}

function prep_aliases(){
  REGISTRY=$(kli vc registry list --name "${KEYSTORE_NAME}" | awk '{print $1}') # Get the first column which is the registry name
  if [ -n "${REGISTRY}" ]; then
      print_dark_gray "Designated Aliases attestation registry already created"
  else
    create_desg_aliases_registry
  fi
  # Add self-attested DIDs for the controller AID
  SAID=$(kli vc list --name "${KEYSTORE_NAME}" --alias "${AID_ALIAS}" --issued --said \
        --schema "${DESG_ALIASES_SCHEMA}")
    if [ -n "${SAID}" ]; then
        print_dark_gray "Designated aliases credential already created"
    else
      create_designated_aliases_json
      create_desg_aliases_cred
    fi
}
prep_aliases

# View issued designated aliases VC
echo
kli vc list --name "${KEYSTORE_NAME}" --alias "${AID_ALIAS}" --issued \
  --schema "${DESG_ALIASES_SCHEMA}"
echo

# generate controller did:webs for DOMAIN
# example: did:webs:127.0.0.1%3A7677:dws:EBFn5ge82EQwxp9eeje-UMEXF-v-3dlfbdVMX_PNjSft
MY_DID="did:webs:${DOMAIN}%3A${DID_PORT}:${ARTIFACT_PATH}:${MY_AID}"
print_yellow "Generating did:webs DID for ${KEYSTORE_NAME} on ${DOMAIN} with AID ${MY_AID} in ${WEB_DIR}/${ARTIFACT_PATH}"
print_yellow "       of: ${MY_DID}"

if [[ "${METADATA_TRUE}" = true ]] ; then
  print_yellow "Using metadata for generation"
  dkr did webs generate \
  --name "${KEYSTORE_NAME}" \
  --output-dir "${WEB_DIR}/${ARTIFACT_PATH}" \
  --did "${MY_DID}" \
  --da_reg "${DESG_ALIASES_REG}" \
  --meta # include DID generation metadata as envelope of DID document in did.json
else
  print_yellow "Not using metadata for generation"
  dkr did webs generate \
  --name "${KEYSTORE_NAME}" \
  --output-dir "${WEB_DIR}/${ARTIFACT_PATH}" \
  --did "${MY_DID}" \
  --da_reg "${DESG_ALIASES_REG}"
fi

resolver_service_pid=""
dkr did webs resolver-service \
  --name "${KEYSTORE_NAME}" \
  --config-dir="${CONFIG_DIR}/controller" \
  --config-file "${KEYSTORE_NAME}" \
  --static-files-dir "${WEB_DIR}" &
resolver_service_pid=$!

# Sample DID: "did:webs:127.0.0.1%3A7677:dws:EBFn5ge82EQwxp9eeje-UMEXF-v-3dlfbdVMX_PNjSft
status=0
if [[ "${METADATA_TRUE}" = true ]] ; then
  print_yellow "Using metadata for resolution"
  dkr did webs resolve --name "${KEYSTORE_NAME}" \
    --did "${MY_DID}" \
    --meta # include DID resolution metadata as envelope of DID document in did.json
  status=$?
else
  print_yellow "Not using metadata for resolution"
  dkr did webs resolve --name "${KEYSTORE_NAME}" \
    --did "${MY_DID}"
  status=$?
fi

kill -9 $resolver_service_pid

if [ $status -ne 0 ]; then
    print_red "DID resolution failed for ${MY_DID}"
    exit 1
else
    print_green "DID resolution succeeded for ${MY_DID}"
fi
