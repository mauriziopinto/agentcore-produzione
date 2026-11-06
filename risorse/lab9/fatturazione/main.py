"""Lab 9: lo specialista fatturazione come agente a sé, su un suo Runtime, con il protocollo A2A.

Nella realtà lo gestirebbe un altro team. Ha il suo ruolo IAM e vede solo gli strumenti
di fatturazione del Gateway. Chi lo chiama non sa come è fatto dentro: legge la sua agent card
e gli manda messaggi A2A.
"""
from strands import Agent
from strands.multiagent.a2a.executor import StrandsA2AExecutor
from bedrock_agentcore.runtime import serve_a2a

from gateway_client import get_gateway_client
from model.load import load_model

SYSTEM_PROMPT = """Sei lo specialista fatturazione di TelcoCare, un operatore di telecomunicazioni di fantasia.
Ti occupi solo di fatture e pagamenti. Rispondi in italiano, in modo breve, senza emoji.
Leggi sempre i dati dal CRM e non inventarli. Non puoi emettere accrediti."""


def create_agent(context_id: str) -> Agent:
    return Agent(
        name="fatturazione",
        description="Specialista fatturazione TelcoCare: legge fatture e pagamenti dei clienti dal CRM.",
        model=load_model(),
        system_prompt=SYSTEM_PROMPT,
        tools=[get_gateway_client(consentiti=["crm___get_cliente", "crm___get_fatture"])],
        callback_handler=None,
    )


# serve_a2a ascolta su 0.0.0.0:9000, come chiede AgentCore per il protocollo A2A,
# e pubblica l'agent card su /.well-known/agent-card.json.
if __name__ == "__main__":
    serve_a2a(StrandsA2AExecutor(agent_factory=create_agent))
