from strands.models.bedrock import BedrockModel


def load_model() -> BedrockModel:
    """Get Bedrock model client using IAM credentials.

    Lab 2: passiamo a Claude Haiku 4.5, più veloce e meno caro di Sonnet.
    Prima di servirlo ai clienti va provato con la stessa serie di prove del Lab 1."""
    return BedrockModel(model_id="global.anthropic.claude-haiku-4-5-20251001-v1:0")
