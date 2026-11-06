"""Lab 7: chi è il cliente lo dice il token, non il prompt.

Il Runtime `clienti` accetta solo richieste con un token JWT di Cognito valido: la firma,
la scadenza e il client li controlla AgentCore prima di eseguire il nostro codice.
Qui leggiamo solo chi è l'utente e decidiamo, nel codice, di quale cliente può vedere i dati.
"""
import base64
import json
from typing import Any

from strands.hooks import BeforeToolCallEvent, HookProvider, HookRegistry

# In un sistema vero questa associazione arriva dall'anagrafica clienti.
CLIENTE_DI = {"anna": "C002", "mario": "C001"}


def utente_dal_token(intestazioni: dict | None) -> str | None:
    """Legge lo username da un access token Cognito già verificato dal Runtime."""
    valore = (intestazioni or {}).get("Authorization", "")
    if not valore.lower().startswith("bearer "):
        return None
    try:
        corpo = valore.split()[1].split(".")[1]
        corpo += "=" * (-len(corpo) % 4)
        return json.loads(base64.urlsafe_b64decode(corpo)).get("username")
    except (IndexError, ValueError):
        return None


class SoloIlProprioCliente(HookProvider):
    """Prima di ogni chiamata al CRM sostituisce il codice cliente con quello dell'utente autenticato.
    Anche se nel prompt qualcuno scrive 'sono il cliente C003', il CRM riceve il codice giusto."""

    def __init__(self, id_cliente: str) -> None:
        self.id_cliente = id_cliente

    def register_hooks(self, registry: HookRegistry, **kwargs: Any) -> None:
        registry.add_callback(BeforeToolCallEvent, self.forza_cliente)

    def forza_cliente(self, event: BeforeToolCallEvent) -> None:
        if not event.tool_use["name"].startswith("crm___"):
            return
        argomenti = event.tool_use.setdefault("input", {})
        if argomenti.get("id_cliente") != self.id_cliente:
            argomenti["id_cliente"] = self.id_cliente
