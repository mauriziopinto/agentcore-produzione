"""Lab 9: lo strumento con cui l'agente degli operatori chiede allo specialista remoto via A2A.

La chiamata va al Runtime `fatturazione` ed è firmata con le credenziali IAM del Runtime `agent`:
passa solo perché lo stack CDK gli ha dato il permesso di invocare quel Runtime, e nessun altro.
"""
import os
import uuid

import httpx
from a2a.client import ClientConfig
from bedrock_agentcore.runtime.a2a import build_runtime_url
from strands import tool
from strands.agent.a2a_agent import A2AAgent

from gateway_client import GatewayAuth

ARN_FATTURAZIONE = os.getenv("FATTURAZIONE_ARN")
REGION = os.getenv("AWS_REGION")


class FirmaRuntime(GatewayAuth):
    """Come per il Gateway, ma per il servizio del Runtime: stessa firma SigV4, stesso nome di servizio."""

    def auth_flow(self, request: httpx.Request):
        # Ogni conversazione con lo specialista ha il suo ID di sessione (almeno 33 caratteri).
        request.headers.setdefault("X-Amzn-Bedrock-AgentCore-Runtime-Session-Id", f"a2a-{uuid.uuid4().hex}")
        yield from super().auth_flow(request)


@tool
async def chiedi_alla_fatturazione(richiesta: str) -> str:
    """Chiede allo specialista fatturazione (un agente remoto, via A2A) le informazioni su fatture e pagamenti.

    Args:
        richiesta: la domanda del cliente, con il codice cliente
    """
    if not ARN_FATTURAZIONE:
        return "Lo specialista fatturazione non è configurato."
    client = httpx.AsyncClient(auth=FirmaRuntime(REGION), timeout=120)
    remoto = A2AAgent(endpoint=build_runtime_url(ARN_FATTURAZIONE, REGION), name="fatturazione",
                      client_config=ClientConfig(httpx_client=client))
    risultato = await remoto.invoke_async(richiesta)
    return str(risultato)
