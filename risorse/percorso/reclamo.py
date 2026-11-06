"""Lab 6: la gestione di un reclamo come grafo a passi fissi, con un evaluator finale.

I passi e il loro ordine li decide il codice (gli archi del grafo), non il modello:
  verifica -> [solo se c'è un addebito errato] rimborso -> redattore -> evaluator
                                                              ^            |
                                                              +-- da rifare +
Il modello lavora solo dentro i singoli passi. L'evaluator (pattern evaluator-optimizer)
legge la bozza di risposta e la rimanda al redattore se non rispetta le regole.
"""
from strands import Agent
from strands.multiagent import GraphBuilder

from gateway_client import get_gateway_client
from model.load import load_model

STILE = "Scrivi sempre in italiano, senza emoji."


def _testo(state, nodo: str) -> str:
    risultato = state.results.get(nodo)
    return str(risultato.result) if risultato is not None else ""


# Condizioni degli archi: codice Python, deterministico, nessuna chiamata al modello.
def addebito_errato(state) -> bool:
    return "ADDEBITO_ERRATO: SI" in _testo(state, "verifica").upper()


def nessun_addebito_errato(state) -> bool:
    return not addebito_errato(state)


def da_rifare(state) -> bool:
    return "DA RIFARE" in _testo(state, "evaluator").upper()


def costruisci_grafo():
    verifica = Agent(
        name="verifica", model=load_model(), callback_handler=None,
        tools=[get_gateway_client(consentiti=["crm___get_cliente", "crm___get_fatture"])],
        system_prompt=f"""Verifichi i reclami sulle fatture di TelcoCare. {STILE}
Leggi cliente e fatture dal CRM. Rispondi con un riepilogo dei fatti, poi su una riga a parte scrivi
esattamente ADDEBITO_ERRATO: SI oppure ADDEBITO_ERRATO: NO, e se SI l'importo in eccesso in euro.""",
    )
    rimborso = Agent(
        name="rimborso", model=load_model(), callback_handler=None,
        tools=[get_gateway_client(consentiti=["crm___emetti_accredito"])],
        system_prompt=f"""Registri l'accredito per un addebito errato già verificato. {STILE}
Usa l'importo in eccesso indicato dalla verifica, arrotondato all'euro intero più vicino. Non registrare altro.""",
    )
    redattore = Agent(
        name="redattore", model=load_model(), callback_handler=None,
        system_prompt=f"""Scrivi la risposta finale al cliente sul suo reclamo, dandogli del Lei. {STILE}
Usa solo i fatti dei passi precedenti. Se l'evaluator ti ha chiesto correzioni, applicale tutte.""",
    )
    evaluator = Agent(
        name="evaluator", model=load_model(), callback_handler=None,
        system_prompt=f"""Controlli la risposta del redattore prima che arrivi al cliente. {STILE}
Regole: deve citare il numero della fattura; se c'è stato un accredito deve indicarne l'importo esatto;
non deve promettere tempi o sconti non registrati; non deve superare 120 parole.
Se tutte le regole sono rispettate rispondi solo APPROVATO. Altrimenti rispondi DA RIFARE seguito
dall'elenco delle correzioni.""",
    )

    g = GraphBuilder()
    g.add_node(verifica, "verifica")
    g.add_node(rimborso, "rimborso")
    g.add_node(redattore, "redattore")
    g.add_node(evaluator, "evaluator")
    g.add_edge("verifica", "rimborso", condition=addebito_errato)
    g.add_edge("verifica", "redattore", condition=nessun_addebito_errato)
    g.add_edge("rimborso", "redattore")
    g.add_edge("redattore", "evaluator")
    g.add_edge("evaluator", "redattore", condition=da_rifare)
    g.set_entry_point("verifica")
    # Limiti obbligatori con un ciclo nel grafo: al massimo 8 passi e 3 minuti in tutto.
    g.set_max_node_executions(8)
    g.set_execution_timeout(180)
    g.set_node_timeout(60)
    g.reset_on_revisit(True)
    return g.build()


async def gestisci_reclamo(testo_reclamo: str) -> tuple[str, dict]:
    grafo = costruisci_grafo()
    risultato = await grafo.invoke_async(testo_reclamo)
    ordine = [n.node_id for n in risultato.execution_order]
    # La risposta è l'ultima bozza del redattore, quella che l'evaluator ha visto per ultima.
    ultima_bozza = ""
    nodo = risultato.results.get("redattore")
    if nodo is not None:
        ultima_bozza = str(nodo.result)
    uso = risultato.accumulated_usage
    esito_controllo = str(risultato.results["evaluator"].result).strip() if "evaluator" in risultato.results else ""
    return ultima_bozza, {
        "percorso": " -> ".join(ordine),
        "stato": str(risultato.status),
        "controllo_finale": esito_controllo[:200],
        "token_input": uso.get("inputTokens", 0),
        "token_output": uso.get("outputTokens", 0),
        "passi": len(ordine),
    }
