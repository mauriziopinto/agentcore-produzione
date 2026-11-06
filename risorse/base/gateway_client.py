"""Client MCP verso AgentCore Gateway, autenticato con IAM (SigV4).

Il deploy imposta nel Runtime la variabile AGENTCORE_GATEWAY_STRUMENTI_URL
e concede al ruolo del Runtime il permesso di chiamare il Gateway.
Ogni richiesta MCP viene firmata con le credenziali AWS del Runtime.
Codice ripreso dal tutorial ufficiale "Build, deploy, and operate an agent".
"""
import os

import httpx
from botocore.auth import SigV4Auth
from botocore.awsrequest import AWSRequest
from botocore.session import Session
from mcp.client.streamable_http import streamablehttp_client
from strands.tools.mcp import MCPClient

GATEWAY_URL = os.getenv("AGENTCORE_GATEWAY_STRUMENTI_URL")
REGION = os.getenv("AWS_REGION")

# Con il CLI 1.0.1 la variabile contiene solo l'host del Gateway, senza il
# percorso. Il server MCP risponde su /mcp: lo aggiungiamo se manca.
if GATEWAY_URL and not GATEWAY_URL.rstrip("/").endswith("/mcp"):
    GATEWAY_URL = GATEWAY_URL.rstrip("/") + "/mcp"


class GatewayAuth(httpx.Auth):
    requires_request_body = True

    def __init__(self, region: str):
        self._credentials = Session().get_credentials()
        self._region = region

    def auth_flow(self, request: httpx.Request):
        signed = AWSRequest(
            method=request.method,
            url=str(request.url),
            data=request.content,
            headers={
                "host": request.url.host,
                "content-type": request.headers.get("content-type", ""),
            },
        )
        SigV4Auth(
            self._credentials.get_frozen_credentials(),
            "bedrock-agentcore",
            self._region,
        ).add_auth(signed)
        request.headers.update(dict(signed.headers))
        yield request


def get_gateway_client() -> MCPClient | None:
    if not GATEWAY_URL:
        return None
    return MCPClient(
        lambda: streamablehttp_client(
            GATEWAY_URL,
            auth=GatewayAuth(REGION),
        )
    )
