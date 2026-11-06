import os

from strands.models.bedrock import BedrockModel


def load_model() -> BedrockModel:
    """Get Bedrock model client using IAM credentials.

    Lab 8: se il deploy ha passato un guardrail, ogni risposta del modello passa dal guardrail,
    che maschera email e numeri di telefono prima che arrivino al cliente."""
    guardrail = os.getenv("GUARDRAIL_ID")
    if not guardrail:
        return BedrockModel(model_id="global.anthropic.claude-sonnet-5-5")
    return BedrockModel(
        model_id="global.anthropic.claude-sonnet-5-5",
        guardrail_id=guardrail,
        guardrail_version=os.getenv("GUARDRAIL_VERSIONE", "1"),
        guardrail_trace="enabled",
        # Il guardrail controlla solo l'ultimo messaggio, non tutta la conversazione a ogni turno.
        guardrail_latest_message=True,
        # Lo streaming aspetta il guardrail: nessun pezzo di testo esce prima del controllo.
        guardrail_stream_processing_mode="sync",
    )
