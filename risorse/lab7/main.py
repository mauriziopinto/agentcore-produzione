"""Lab 7: il canale dei clienti. Un secondo Runtime, protetto da token Cognito.

Differenze rispetto al Runtime `agent` degli operatori:
- l'utente arriva dal token verificato da AgentCore, non dal campo actorId del payload;
- la Memory è separata per utente vero;
- il CRM riceve sempre il codice cliente dell'utente autenticato;
- il cliente non vede lo strumento per emettere accrediti.
"""
from functools import lru_cache

from strands import Agent
from strands.agent.conversation_manager.null_conversation_manager import NullConversationManager
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from model.load import load_model
from parse import parse_payload
from memory.session import get_memory_session_manager
from gateway_client import get_gateway_client
from identita import CLIENTE_DI, SoloIlProprioCliente, utente_dal_token

STRUMENTI_CLIENTE = ["crm___get_cliente", "crm___get_fatture", "crm___apri_ticket"]


@lru_cache(maxsize=128)
def _get_agent(session_id: str, utente: str) -> Agent:
    id_cliente = CLIENTE_DI[utente]
    return Agent(
        model=load_model(),
        session_manager=get_memory_session_manager(session_id, utente),
        conversation_manager=NullConversationManager(),
        system_prompt=f"""Sei l'assistente clienti di TelcoCare, un operatore di telecomunicazioni di fantasia.
Rispondi sempre in italiano, in modo breve e cordiale, senza emoji.
Stai parlando con il cliente {id_cliente}: usa sempre questo codice e non inventare dati.
Non puoi emettere accrediti: se servono, apri un ticket per un operatore.""",
        tools=[get_gateway_client(consentiti=STRUMENTI_CLIENTE)],
        hooks=[SoloIlProprioCliente(id_cliente)],
    )


def create_app():
    app = BedrockAgentCoreApp()
    log = app.logger

    @app.entrypoint
    async def invoke(payload, context):
        utente = utente_dal_token(getattr(context, "request_headers", None))
        if utente not in CLIENTE_DI:
            yield {"event": {"contentBlockDelta": {"delta": {"text": "Utente non riconosciuto."}}}}
            return
        session_id = getattr(context, "session_id", None) or "default-session"
        prompt, actor_dichiarato = parse_payload(payload)
        log.info(f"Utente dal token: {utente}; actorId scritto nel payload e ignorato: {actor_dichiarato}")
        async for event in _get_agent(session_id, utente).stream_async(prompt):
            if not isinstance(event, dict) or "event" not in event:
                continue
            cbs = event["event"].get("contentBlockStart")
            if cbs is not None and not cbs.get("start"):
                continue
            yield event

    return app


app = create_app()
if __name__ == "__main__":
    app.run()
