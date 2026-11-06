"""Lab 11: uno swarm, cioè agenti che si passano il lavoro da soli, e i limiti che lo tengono a bada.

Nello swarm non c'è un supervisore né un ordine dei passi: ogni agente decide se rispondere
o passare il caso a un altro con lo strumento handoff_to_agent. Niente nella struttura impedisce
ai due agenti di rimbalzarsi il caso: per questo i limiti sono obbligatori.
"""
from strands import Agent
from strands.multiagent import Swarm

from gateway_client import get_gateway_client
from model.load import load_model

STILE = "Scrivi sempre in italiano, senza emoji, in modo breve."


# Istruzioni scritte male di proposito: ognuno dei due vuole sempre il parere dell'altro.
# Così si vede cosa succede a uno swarm quando i compiti si sovrappongono.
RIMBALZO = "Se la richiesta tocca anche solo in parte l'altro ambito, prima di rispondere passa sempre il caso all'altro collega."


def costruisci_sciame(limiti_stretti: bool = True, rimbalzo: bool = False) -> Swarm:
    extra = RIMBALZO if rimbalzo else ""
    fatturazione = Agent(
        name="fatturazione", model=load_model(), callback_handler=None,
        description="Specialista di fatture, pagamenti e accrediti.",
        tools=[get_gateway_client(consentiti=["crm___get_cliente", "crm___get_fatture"])],
        system_prompt=f"""Sei lo specialista fatturazione di TelcoCare. {STILE}
Ti occupi solo di fatture e pagamenti. Per qualunque aspetto tecnico passa il caso al tecnico. {extra}""",
    )
    tecnico = Agent(
        name="tecnico", model=load_model(), callback_handler=None,
        description="Specialista di guasti, linee e modem.",
        tools=[get_gateway_client(consentiti=["crm___get_cliente", "crm___apri_ticket"])],
        system_prompt=f"""Sei lo specialista tecnico di TelcoCare. {STILE}
Ti occupi solo di guasti e linee. Per qualunque aspetto economico passa il caso alla fatturazione. {extra}""",
    )
    if limiti_stretti:
        return Swarm(
            [fatturazione, tecnico],
            entry_point=fatturazione,
            max_handoffs=4,                         # passaggi fra agenti, in tutto
            max_iterations=6,                       # turni di agente, in tutto
            execution_timeout=120.0,                # secondi per l'intero swarm
            node_timeout=60.0,                      # secondi per un singolo turno
            repetitive_handoff_detection_window=4,  # guarda gli ultimi 4 passaggi...
            repetitive_handoff_min_unique_agents=2, # ...e ferma il ping-pong fra 2 soli agenti
        )
    return Swarm([fatturazione, tecnico], entry_point=fatturazione)


async def gestisci_caso(testo: str, limiti_stretti: bool = True, rimbalzo: bool = False) -> tuple[str, dict]:
    sciame = costruisci_sciame(limiti_stretti, rimbalzo)
    risultato = await sciame.invoke_async(testo)
    percorso = [n.node_id for n in risultato.node_history]
    ultimo = percorso[-1] if percorso else ""
    risposta = str(risultato.results[ultimo].result) if ultimo in risultato.results else ""
    uso = risultato.accumulated_usage
    return risposta, {
        "percorso": " -> ".join(percorso),
        "stato": str(risultato.status),
        "passaggi": max(0, len(percorso) - 1),
        "token_input": uso.get("inputTokens", 0),
        "token_output": uso.get("outputTokens", 0),
    }
