"""Lab 4: tre modi di rispondere alla stessa domanda, con il conto dei token per ogni agente.

- singolo:     un agente con tutti gli strumenti (come TelcoCare finora, senza Memory).
- supervisore: un agente che delega a due specialisti, usati come strumenti (agents as tools).
- instradato:  una regola sceglie lo specialista senza chiamare il modello; solo i casi
               che la regola non riconosce salgono al supervisore (hybrid supervisor).

Ogni agente ha un nome; il conto dei token si tiene per nome, così si vede quanto costa
ciascuno. La Memory è spenta in tutti e tre i modi, perché il confronto sia alla pari.
"""
import re
import time

from strands import Agent, tool

from gateway_client import get_gateway_client
from model.load import load_model
from remoto import chiedi_alla_fatturazione

STILE = "Rispondi sempre in italiano, in modo breve e cordiale, senza emoji. Non inventare dati sui clienti."

PROMPT_SINGOLO = f"""Sei l'assistente clienti di TelcoCare, un operatore di telecomunicazioni di fantasia.
{STILE}
Per gli strumenti del CRM ti serve il codice cliente (per esempio C001): se non lo conosci, chiedilo."""

PROMPT_FATTURE = f"""Sei lo specialista fatturazione di TelcoCare. Ti occupi solo di fatture, pagamenti e accrediti.
{STILE}
Leggi sempre le fatture dal CRM prima di rispondere. Non registrare accrediti se non te lo chiedono esplicitamente."""

PROMPT_TECNICO = f"""Sei lo specialista dell'assistenza tecnica di TelcoCare. Ti occupi solo di guasti, linee e modem.
{STILE}
Controlla le linee del cliente nel CRM. Se c'è un guasto, apri un ticket con una descrizione chiara."""

PROMPT_SUPERVISORE = f"""Sei il supervisore dell'assistenza clienti di TelcoCare.
{STILE}
Non hai accesso diretto al CRM: delega allo specialista giusto e passagli il codice cliente.
Se la richiesta riguarda sia fatture sia guasti, consulta entrambi e unisci le risposte."""

# Regole dell'instradamento deterministico: parole chiave, nessuna chiamata al modello.
PAROLE_FATTURE = re.compile(r"fattur|accredit|addebit|pagament|sollecit|bollett|rimbors", re.I)
PAROLE_TECNICO = re.compile(r"guast|lent|connession|non funziona|non va|modem|linea|ticket", re.I)


class Conto:
    """Somma token e chiamate al modello per ogni agente di una richiesta."""

    def __init__(self) -> None:
        self.per_agente: dict[str, dict] = {}
        self.inizio = time.time()

    def aggiungi(self, nome: str, risultato) -> None:
        uso = risultato.metrics.accumulated_usage
        voce = self.per_agente.setdefault(nome, {"input": 0, "output": 0, "chiamate_modello": 0})
        voce["input"] += uso.get("inputTokens", 0)
        voce["output"] += uso.get("outputTokens", 0)
        voce["chiamate_modello"] += risultato.metrics.cycle_count

    def riepilogo(self, modalita: str, percorso: str) -> dict:
        totale_in = sum(v["input"] for v in self.per_agente.values())
        totale_out = sum(v["output"] for v in self.per_agente.values())
        return {
            "modalita": modalita,
            "percorso": percorso,
            "secondi": round(time.time() - self.inizio, 1),
            "token_input": totale_in,
            "token_output": totale_out,
            "chiamate_modello": sum(v["chiamate_modello"] for v in self.per_agente.values()),
            "per_agente": self.per_agente,
        }


def _specialista(nome: str, prompt: str, strumenti: list[str]) -> Agent:
    return Agent(
        name=nome,
        model=load_model(),
        system_prompt=prompt,
        tools=[get_gateway_client(consentiti=strumenti)],
        callback_handler=None,
    )


def _fatturazione() -> Agent:
    return _specialista("fatturazione", PROMPT_FATTURE,
                        ["crm___get_cliente", "crm___get_fatture", "crm___emetti_accredito"])


def _tecnico() -> Agent:
    return _specialista("tecnico", PROMPT_TECNICO, ["crm___get_cliente", "crm___apri_ticket"])


async def singolo(domanda: str) -> tuple[str, dict]:
    conto = Conto()
    agente = Agent(name="singolo", model=load_model(), system_prompt=PROMPT_SINGOLO,
                   tools=[get_gateway_client()], callback_handler=None)
    risultato = await agente.invoke_async(domanda)
    conto.aggiungi("singolo", risultato)
    return str(risultato), conto.riepilogo("singolo", "singolo")


async def supervisore(domanda: str, conto: Conto | None = None, percorso: str = "supervisore") -> tuple[str, dict]:
    conto = conto or Conto()

    @tool
    async def chiedi_a_fatturazione(richiesta: str) -> str:
        """Delega allo specialista fatturazione: fatture, pagamenti, solleciti, accrediti.

        Args:
            richiesta: la richiesta del cliente, con il codice cliente
        """
        risultato = await _fatturazione().invoke_async(richiesta)
        conto.aggiungi("fatturazione", risultato)
        return str(risultato)

    @tool
    async def chiedi_al_tecnico(richiesta: str) -> str:
        """Delega allo specialista tecnico: guasti, linee lente o ferme, modem, ticket.

        Args:
            richiesta: la richiesta del cliente, con il codice cliente
        """
        risultato = await _tecnico().invoke_async(richiesta)
        conto.aggiungi("tecnico", risultato)
        return str(risultato)

    capo = Agent(name="supervisore", model=load_model(), system_prompt=PROMPT_SUPERVISORE,
                 tools=[chiedi_a_fatturazione, chiedi_al_tecnico], callback_handler=None)
    risultato = await capo.invoke_async(domanda)
    conto.aggiungi("supervisore", risultato)
    return str(risultato), conto.riepilogo("supervisore", percorso)


async def instradato(domanda: str) -> tuple[str, dict]:
    fatture = bool(PAROLE_FATTURE.search(domanda))
    tecnico = bool(PAROLE_TECNICO.search(domanda))
    conto = Conto()
    if fatture and not tecnico:
        risultato = await _fatturazione().invoke_async(domanda)
        conto.aggiungi("fatturazione", risultato)
        return str(risultato), conto.riepilogo("instradato", "regola -> fatturazione")
    if tecnico and not fatture:
        risultato = await _tecnico().invoke_async(domanda)
        conto.aggiungi("tecnico", risultato)
        return str(risultato), conto.riepilogo("instradato", "regola -> tecnico")
    # La regola non basta (nessuna parola chiave, o entrambe): decide il supervisore.
    return await supervisore(domanda, conto, percorso="regola incerta -> supervisore")


async def remoto(domanda: str) -> tuple[str, dict]:
    """Lab 9: lo specialista fatturazione è un agente remoto, su un altro Runtime, raggiunto via A2A."""
    conto = Conto()

    @tool
    async def chiedi_al_tecnico(richiesta: str) -> str:
        """Delega allo specialista tecnico: guasti, linee lente o ferme, modem, ticket.

        Args:
            richiesta: la richiesta del cliente, con il codice cliente
        """
        risultato = await _tecnico().invoke_async(richiesta)
        conto.aggiungi("tecnico", risultato)
        return str(risultato)

    capo = Agent(name="supervisore", model=load_model(), system_prompt=PROMPT_SUPERVISORE,
                 tools=[chiedi_alla_fatturazione, chiedi_al_tecnico], callback_handler=None)
    risultato = await capo.invoke_async(domanda)
    conto.aggiungi("supervisore", risultato)
    # I token dello specialista remoto li paga e li vede il suo Runtime, non questo.
    return str(risultato), conto.riepilogo("remoto", "supervisore + fatturazione via A2A")


MODALITA = {"singolo": singolo, "supervisore": supervisore, "instradato": instradato, "remoto": remoto}
