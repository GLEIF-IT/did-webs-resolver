
# did:webS - A More Secure did:web, a More Discoverable did:keri

[![hackmd-github-sync-badge](https://hackmd.io/dbB7E1bPSPGZ_Ow5S_9pmg/badge)](https://hackmd.io/dbB7E1bPSPGZ_Ow5S_9pmg)

did:webS is a new DID Method that intends to combine the security of the Key Event Receipt Infrastruture (KERI) with
the ease of use and discoverability of did:web.  The intention is to rely on KERI key management to create and manage
identifiers (called Autonomic IDentifiers (AIDs) in KERI) and expose them as DIDs that look and behave like did:web
DIDs via this DID Method.  

## CRUD Methods
KERI protocol should be used for the CUD in CRUD and web access for the R.

## DID Document
This document specifies the algorithm for generating a DID Document from a KERI AID.  The first (and most obvious) source
of data used to generate a DID Document is the key event log (KEL) of the AID.  The key event log represents a cryptographic chain
of custody from the AID itself down to the current set of signing keys and next rotation key commitments.  When generating a
DID Document an implementation must "walk the KEL" to determine the current key state.  Due to the fact that the KERI protocol
allows for non-establishment event (events that don't change key state) to be intermixed in a KEL with establishment 
events (those that change key state), the last event may not be an establishment event and thus can not be relied on to
provide key information.  In addition, the current set of witnesses is calculated from the initial set declared in the 
inception event and "adds" and "cuts" declared in rotation events.

In KERI the calcuated values that result from walking the KEL is refered to as the "current key state" and is expressed
in the Key State Notice (KSN) record.  An example of a KSN can be seen here:

```json
{
    "v": "KERI10JSON000274_",
    "i": "EeS834LMlGVEOGR8WU3rzZ9M6HUv_vtF32pSXQXKP7jg",
    "s": "1",
    "t": "ksn",
    "p": "ESORkffLV3qHZljOcnijzhCyRT0aXM2XHGVoyd5ST-Iw",
    "d": "EtgNGVxYd6W0LViISr7RSn6ul8Yn92uyj2kiWzt51mHc",
    "f": "1",
    "dt": "2021-11-04T12:55:14.480038+00:00",
    "et": "ixn",
    "kt": "1",
    "k": [
      "DTH0PwWwsrcO_4zGe7bUR-LJX_ZGBTRsmP-ZeJ7fVg_4"
    ],
    "nt": 1,
    "n": [
      "E6qpfz7HeczuU3dAd1O9gPPS6-h_dCxZGYhU8UaDY2pc"
    ],
    "bt": "3",
    "b": [
      "BGKVzj4ve0VSd8z_AmvhLg4lqcC_9WYX90k03q-R_Ydo",
      "BuyRFMideczFZoapylLIyCjSdhtqVb31wZkRKvPfNqkw",
      "Bgoq68HCmYNUDgOz4Skvlu306o_NY-NrYuKAVhk3Zh9c"
    ],
    "c": [],
    "ee": {
      "s": "0",
      "d": "ESORkffLV3qHZljOcnijzhCyRT0aXM2XHGVoyd5ST-Iw",
      "br": [],
      "ba": []
    },
    "di": ""
}
```

Using this key state as reference, we can identify the fields from the current key state that will translate to values
in the DID Document.  The following table lists the values from the example KSN and their associated values in a DID Document:

| Key State Field | Definition                                            | DID Document Value                                                                           |
|:---------------:|:------------------------------------------------------|:---------------------------------------------------------------------------------------------| 
|       `i`       | The AID value                                         | The value after the last ":" in the DID (both subject and controller)                        |
|       `k`       | The current set of public signing keys                | Verification Methods with associated authentication and assertion verification relationships |
|       `n`       | The current set of pre-rotated key commitment digests | Verification Methods with associated capabilityInvocation verification relationships         | 
|       `b`       | The current set of witness AIDs                       | Service for each witness AID with a type of "witness"                                        |
|      `di`       | The delegator (if any) for this AID                   | Verification method with associated capabilityDelegation verification relationships          |


In several cases above, the value from the key state is not enough by itself to populate the DID Document.  The following
sections detail the algorithm to follow for each case.

### AID Value
The AID value is the single string representation of the identifier.  The algorithm used to generate the AID depends on
the type of AID.  If the AID is transferable (supports key rotation) the AID is generated by taking a cryptographic
digest of the inception event of the KEL of the AID.  If the AID is non-transferable (does not support key rotation) the
AID is generated by taking a cryptographic digest of the first (and only) public key of the identifier (details of these
operations can be found in the KERI Specification (ref?).  

The value from the `i` field MUST be the value after the last `:` in the method specific identifier (MSI) of the DID.  The
rest of the MSI will generated using the rules defined in the DID Web Specification regarding hostname, port and path:

The method specific identifier MUST match the common name used in the SSL/TLS certificate, and it MUST NOT include IP
addresses. A port MAY be included and the colon MUST be percent encoded to prevent a conflict with paths. 
Directories and subdirectories MAY optionally be included, delimited by colons rather than slashes.

webs-did = "did:webs:" domain-name ":" aid
webs-did = "did:webs:" domain-name * (":" path) ":" aid


### Current Set of Public Signing Keys
KERI identifiers represent public signing keys as Composable Event Streaming Representation (CESR) encoded strings in the 
`k` field of establishment events and the key state notice.  CESR encoding encapsulates all the information needed to 
determine the cryptographic algorithm used to generate the key pair.  For each key listed in the array value of the `k` field
a cooresponding Verification Method will be generated in the DID Document.  The 'type' field  in the verification method for each
public key will be determined by the algorithm used to generate the public key.  At the time of this writing, KERI currently
supports 




Signing Keys -> Verification Methods

Service Endpoints -> Services

Blah blah blah


