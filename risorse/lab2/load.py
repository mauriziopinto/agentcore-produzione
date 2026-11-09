from strands.models.bedrock import BedrockModel


def load_model() -> BedrockModel:
    """Get Bedrock model client using IAM credentials.

    Lab 2: passiamo ad Amazon Nova 2 Lite, un modello più piccolo e meno caro di Sonnet.
    Prima di servirlo ai clienti va provato con gli stessi test del Lab 1."""
    return BedrockModel(model_id="global.amazon.nova-2-lite-v1:0")
