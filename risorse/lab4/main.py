from functools import lru_cache

from strands import Agent, tool
from strands.agent.conversation_manager.null_conversation_manager import NullConversationManager
from bedrock_agentcore.runtime import BedrockAgentCoreApp
from model.load import load_model
from parse import parse_payload
from memory.session import get_memory_session_manager
from gateway_client import get_gateway_client
from strumenti_aws import esegui_python, leggi_pagina_web
from approvazione import ApprovazioneAccrediti
from squadra import MODALITA

SYSTEM_PROMPT = """Sei l'assistente clienti di TelcoCare, un operatore di telecomunicazioni di fantasia.
Rispondi sempre in italiano, in modo breve e cordiale, senza emoji.
Usa gli strumenti a disposizione quando servono e non inventare dati sui clienti.
Per gli strumenti del CRM ti serve il codice cliente (per esempio C001): se non lo conosci, chiedilo.
Rispondi solo a domande sui servizi TelcoCare. Per qualunque altra richiesta, spiega con gentilezza che puoi aiutare solo con linee, offerte, fatture e assistenza TelcoCare."""

tools = []


@tool
def calcola_rata(prezzo_euro: float, mesi: int) -> str:
    """Calcola la rata mensile per l'acquisto a rate di uno smartphone, senza interessi.

    Args:
        prezzo_euro: prezzo totale del dispositivo in euro
        mesi: numero di rate mensili (da 1 a 48)
    """
    if mesi < 1 or mesi > 48:
        return "Il numero di rate deve essere compreso fra 1 e 48."
    return f"{mesi} rate da {prezzo_euro / mesi:.2f} euro al mese"


tools.append(calcola_rata)

# Gli strumenti del CRM arrivano dal Gateway
gateway = get_gateway_client()
if gateway:
    tools.append(gateway)

# Code Interpreter e Browser gestiti da AWS
tools.append(esegui_python)
tools.append(leggi_pagina_web)


def _make_conversation_manager():
    return NullConversationManager()


@lru_cache(maxsize=128)
def _get_agent(session_id: str, actor_id: str) -> Agent:
    """Crea (o riusa) un agente per ogni coppia sessione/utente.
    La sessione resta nella stessa microVM: così una richiesta di approvazione
    e la sua risposta trovano lo stesso agente, fermo nello stesso punto."""
    return Agent(
        model=load_model(),
        session_manager=get_memory_session_manager(session_id, actor_id),
        conversation_manager=_make_conversation_manager(),
        system_prompt=SYSTEM_PROMPT,
        tools=tools,
        hooks=[ApprovazioneAccrediti()],
    )


def _input_agente(payload: dict):
    """Una richiesta normale porta un prompt. La risposta di un responsabile porta
    {"approvazione": {"id": "<id dell'interruzione>", "risposta": "approvo" o "rifiuto"}}."""
    approvazione = payload.get("approvazione")
    actor_id = payload.get("actorId") or "default"
    if isinstance(approvazione, dict):
        return [{
            "interruptResponse": {
                "interruptId": str(approvazione.get("id", "")),
                "response": str(approvazione.get("risposta", "rifiuto")),
            }
        }], actor_id
    return parse_payload(payload)


def create_app():
    app = BedrockAgentCoreApp()
    log = app.logger

    @app.entrypoint
    async def invoke(payload, context):
        session_id = getattr(context, "session_id", None) or "default-session"

        # Lab 4: confronto fra agente singolo, supervisore e instradamento deterministico.
        modalita = payload.get("modalita")
        if modalita in MODALITA:
            domanda, _ = parse_payload(payload)
            log.info(f"Modalita {modalita}: session_id={session_id}")
            testo, costo = await MODALITA[modalita](domanda)
            yield {"event": {"contentBlockDelta": {"delta": {"text": testo}}}}
            yield {"costo": costo}
            return

        richiesta, actor_id = _input_agente(payload)
        log.info(f"Invocazione: session_id={session_id} actor_id={actor_id}")
        agent = _get_agent(session_id, actor_id)

        async for event in agent.stream_async(richiesta):
            if isinstance(event, dict) and "result" in event:
                risultato = event["result"]
                if getattr(risultato, "stop_reason", None) == "interrupt":
                    for interruzione in risultato.interrupts:
                        log.info(f"Approvazione richiesta: {interruzione.reason}")
                        yield {"approvazione_richiesta": {"id": interruzione.id, "dettagli": interruzione.reason}}
                continue
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
