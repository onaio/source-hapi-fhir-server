#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#


import sys

from airbyte_cdk.entrypoint import launch
from source_hapi_fhir_server import SourceHapiFhirServer

if __name__ == "__main__":
    source = SourceHapiFhirServer()
    launch(source, sys.argv[1:])
