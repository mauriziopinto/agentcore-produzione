"""Lab 3: un accredito sopra una soglia aspetta l'approvazione di una persona.

Tre livelli per lo stesso strumento:
- fino a SOGLIA_AUTOMATICA euro l'agente procede da solo;
- sopra SOGLIA_AUTOMATICA l'agente si ferma e chiede l'approvazione (questo file);
- sopra i 100 euro il Gateway rifiuta comunque, per la regola Cedar.

Il controllo è un hook di Strands: gira prima di ogni chiamata a uno strumento,
fuori dal ragionamento del modello. Il modello non può saltarlo.
"""
from typing import Any

from strands.hooks import BeforeToolCallEvent, HookProvider, HookRegistry

STRUMENTO = "crm___emetti_accredito"
SOGLIA_AUTOMATICA = 20
NOME_INTERRUZIONE = "telcocare-approvazione-accredito"


class ApprovazioneAccrediti(HookProvider):
    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        registry.add_callback(BeforeToolCallEvent, self.controlla)

    def controlla(self, event: BeforeToolCallEvent) -> None:
        if event.tool_use["name"] != STRUMENTO:
            return
        argomenti = event.tool_use.get("input") or {}
        importo = argomenti.get("importo_euro", 0)
        try:
            importo = float(importo)
        except (TypeError, ValueError):
            event.cancel_tool = "Importo dell'accredito non valido"
            return
        if importo <= SOGLIA_AUTOMATICA:
            return

        # L'agente si ferma qui. Riprende quando arriva la risposta del responsabile.
        risposta = event.interrupt(
            NOME_INTERRUZIONE,
            reason={
                "id_cliente": argomenti.get("id_cliente"),
                "importo_euro": importo,
                "motivo": argomenti.get("motivo"),
            },
        )
        if str(risposta).strip().lower() != "approvo":
            event.cancel_tool = "Il responsabile non ha approvato l'accredito"
