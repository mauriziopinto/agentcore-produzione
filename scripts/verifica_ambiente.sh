#!/usr/bin/env bash
# Lab 0: controlla che l'ambiente abbia tutto quello che serve al workshop.
# Non crea risorse: legge versioni e fa una chiamata di prova a ognuno dei due modelli del workshop.
# La prima chiamata a un modello Anthropic attiva la sottoscrizione AWS Marketplace per tutto l'account,
# e deve partire da chi ha i permessi aws-marketplace:Subscribe, cioè da te e non dal ruolo del Runtime.
# Per questo il modello del Lab 2 (Claude Haiku 4.5) si chiama qui, anche se l'agente lo userà solo dopo.

REGIONE="${AWS_REGION:-us-east-1}"
MODELLI="global.anthropic.claude-sonnet-5-5 global.anthropic.claude-haiku-4-5-20251001-v1:0"
CLI_TESTATA="1.0.1"
ERRORI=0

ok()   { printf "  [ok]  %s\n" "$1"; }
ko()   { printf "  [NO]  %s\n" "$1"; ERRORI=$((ERRORI + 1)); }
nota() { printf "  [!!]  %s\n" "$1"; }

echo "Verifica dell'ambiente per il workshop AgentCore (regione $REGIONE)"
echo

if IDENTITA=$(aws sts get-caller-identity --query Arn --output text 2>/dev/null); then
  ok "credenziali AWS: $IDENTITA"
else
  ko "credenziali AWS non configurate (aws sts get-caller-identity fallisce)"
fi

if [ "$REGIONE" = "us-east-1" ]; then
  ok "regione us-east-1"
else
  nota "AWS_REGION vale $REGIONE: il workshop è stato provato in us-east-1"
fi

if command -v node >/dev/null 2>&1; then ok "Node.js $(node --version)"; else ko "Node.js mancante"; fi
if command -v uv >/dev/null 2>&1; then ok "uv $(uv --version | awk '{print $2}')"; else ko "uv mancante"; fi
if command -v python3 >/dev/null 2>&1; then ok "Python $(python3 --version | awk '{print $2}')"; else ko "python3 mancante"; fi

if command -v agentcore >/dev/null 2>&1; then
  VERSIONE=$(agentcore --version 2>/dev/null)
  if [ "$VERSIONE" = "$CLI_TESTATA" ]; then
    ok "AgentCore CLI $VERSIONE"
  else
    nota "AgentCore CLI $VERSIONE: i lab sono stati provati con la $CLI_TESTATA, qualche messaggio può essere diverso"
  fi
else
  ko "AgentCore CLI mancante (npm install -g @aws/agentcore)"
fi

if python3 -m pip show bedrock-agentcore-starter-toolkit >/dev/null 2>&1; then
  nota "è installato anche il vecchio starter toolkit Python: anche lui si chiama agentcore e può nascondere il CLI giusto"
fi

if command -v kiro-cli >/dev/null 2>&1; then ok "Kiro CLI $(kiro-cli --version 2>/dev/null | awk '{print $NF}')"; else nota "Kiro CLI non trovato (serve solo per gli esercizi facoltativi)"; fi

echo
for MODELLO in $MODELLI; do
  echo "Chiamata di prova al modello $MODELLO..."
  RISPOSTA=$(aws bedrock-runtime converse --region "$REGIONE" --model-id "$MODELLO" \
    --messages '[{"role":"user","content":[{"text":"Rispondi solo con la parola: pronto"}]}]' \
    --query 'output.message.content[0].text' --output text 2>&1)
  if [ $? -eq 0 ]; then
    ok "il modello risponde: $RISPOSTA"
  else
    ko "il modello non risponde: $RISPOSTA"
  fi
done

echo
if [ "$ERRORI" -eq 0 ]; then
  echo "Tutto pronto. Ora lancia: bash scripts/prepara_base.sh"
else
  echo "Ci sono $ERRORI problemi da risolvere prima di continuare: chiama chi conduce il workshop."
  exit 1
fi
