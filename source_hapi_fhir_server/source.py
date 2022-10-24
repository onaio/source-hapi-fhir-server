#
# Copyright (c) 2022 Airbyte, Inc., all rights reserved.
#

from abc import ABC
from typing import Any, Iterable, List, Mapping, MutableMapping, Optional, Tuple
from urllib import parse

import requests
from airbyte_cdk.logger import AirbyteLogger
from airbyte_cdk.sources import AbstractSource
from airbyte_cdk.sources.streams import Stream
from airbyte_cdk.sources.streams.http import HttpStream
from airbyte_cdk.sources.streams.http.auth import TokenAuthenticator


class HapiFhirServerStream(HttpStream, ABC):

    primary_key = "id"
    url_base = "{}"

    def __init__(self, base_url: str, resource_type: str, **kwargs):
        super().__init__(**kwargs)
        self.url_base = base_url
        self.resource_type = resource_type
        self.auth = kwargs["authenticator"]

    def next_page_token(self, response: requests.Response) -> Optional[Mapping[str, Any]]:
        return None

    def request_params(
            self,
            stream_state: Mapping[str, Any],
            stream_slice: Mapping[str, any] = None,
            next_page_token: Mapping[str, Any] = None
    ) -> MutableMapping[str, Any]:
        params = {}
        return params

    def parse_response(
            self,
            response: requests.Response, **kwargs
    ) -> Iterable[Mapping]:
        response_json = response.json()
        for record in response_json.get("entry", []):
            yield record


class Resources(HapiFhirServerStream):
    """
    Handle how resources stream behaves
    """

    def path(self, **kwargs) -> str:
        return self.resource_type


class IncrementalHapiFhirServerStream(HapiFhirServerStream, ABC):

    @property
    def cursor_field(self) -> str:
        return []

    def get_updated_state(self, current_stream_state: MutableMapping[str, Any], latest_record: Mapping[str, Any]) -> Mapping[str, Any]:
        return {}


class SourceHapiFhirServer(AbstractSource):

    @staticmethod
    def get_authenticator(config):
        try:
            response = requests.request(
                method="POST",
                url=config.get("access_token_url"),
                data={
                    "client_id": (None, config.get("client_id")),
                    "client_secret": (None, config.get("client_secret")),
                    "username": (None, config.get("username")),
                    "password": (None, config.get("password")),
                    "scope": (None, "profile"),
                    "grant_type": (None, "client_credentials")
                },
            )
            response.raise_for_status()
            response_body = response.json()
            access_token = response_body["access_token"]
        except Exception as e:
            raise Exception(f"Error while requesting access token: {e}") from e

        auth = TokenAuthenticator(token=access_token, auth_method="Bearer")
        return auth

    def check_connection(
            self,
            logger: AirbyteLogger,
            config: Mapping[str, Any]
    ) -> Tuple[bool, any]:
        try:
            authenticator = self.get_authenticator(config)
            url = parse.urljoin(config.get("base_url"), "metadata")
            response = requests.get(url, headers=authenticator.get_auth_header())

            if response.status_code == requests.codes.ok:
                return True, None
            else:
                return False, response.json()
        except Exception as e:
            return False, f"Got an exception trying to connect: {e}"

    def streams(self, config: Mapping[str, Any]) -> List[Stream]:
        auth = self.get_authenticator(config)
        base_url = config["base_url"]
        resource_type = config["resource_type"]

        return [Resources(authenticator=auth, base_url=base_url, resource_type=resource_type)]
