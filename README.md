# Agenti in produzione, in sicurezza

Repository del secondo workshop su Amazon Bedrock AgentCore. I partecipanti riprendono TelcoCare,
l'assistente clienti di un operatore telco di fantasia costruito nel primo workshop, e lo preparano
per la produzione: test automatici, rilasci reversibili, controlli fuori dal modello, pattern
multi-agente, guasti e retry, identità dell'utente, dati personali, allarmi.

Le istruzioni sono nel sito statico in `docs/`. Le pagine si generano dai file in `docs/_pezzi/`
con `python3 docs/_pezzi/costruisci.py`.

## Percorso

| Parte | Lab |
| --- | --- |
| Partenza | 0 Ripartenza: `scripts/prepara_base.sh` ricrea TelcoCare com'era alla fine del primo workshop |
| In aula | 1 Test prima del rilascio, 2 Rilascio reversibile, 3 Il controllo sta fuori dal modello, 4 Più agenti solo se serve |
| Da soli (72 ore) | 5 Guasti e retry, 6 Grafo ed evaluator, 7 Identità dell'utente, 8 Dati personali, 9 Agenti di team diversi (A2A), 10 Allarmi, 11 Swarm |

I lab da 5 a 11 partono da `scripts/prepara_percorso.sh`, che pubblica un codice comune
(`risorse/percorso/`). Dopo, ogni lab cambia solo l'infrastruttura e l'ordine è libero.

## Contenuto

| Cartella | Contenuto |
| --- | --- |
| `docs/` | Il sito dei lab; `docs/pagine/offerta-novembre.html` è la pagina con l'istruzione nascosta del Lab 3 |
| `risorse/base/` | Il TelcoCare di partenza |
| `risorse/labN/` | I file dei lab in aula e quelli specifici dei lab da soli |
| `risorse/percorso/` | Il codice comune dei lab da 5 a 11 |
| `scripts/` | Script di supporto: preparazione, test e quality gate, endpoint, confronto dei pattern, Cognito, guardrail, log, allarmi, pulizia |
| `infra/sito.yaml` | Pubblicazione del sito: bucket S3 privato e CloudFront con Origin Access Control |

## Requisiti dell'ambiente

Gli stessi del primo workshop: account AWS personale in `us-east-1` con accesso ai modelli
Anthropic su Amazon Bedrock, AgentCore CLI 1.0.1, Node.js, `uv`, Python, AWS CLI. In Code Editor
la porta 8080 è occupata: per `agentcore dev` si usa la 8181.

## Esposizione

Nessuna risorsa creata nei lab è raggiungibile senza autenticazione: Runtime e Gateway usano IAM
(SigV4), il Runtime `clienti` del Lab 7 accetta solo token JWT di un pool Cognito con la
registrazione autonoma disattivata, la Lambda del CRM non ha URL pubblici. Il sito dei lab è
pubblico in sola lettura tramite CloudFront; il bucket resta privato. Tutto si cancella con
`scripts/pulizia.sh`.

## Origine

Il percorso usa la documentazione AWS e Strands come fonte dei pattern:
[Agentic AI Lens](https://docs.aws.amazon.com/wellarchitected/latest/agentic-ai-lens/agentic-ai-lens.html),
[Agentic AI patterns and workflows on AWS](https://docs.aws.amazon.com/prescriptive-guidance/latest/agentic-ai-patterns/introduction.html),
[Tutorial: Build, deploy, and operate an agent](https://docs.aws.amazon.com/bedrock-agentcore/latest/devguide/agentcore-cli-get-started.html),
[Strands multi-agent patterns](https://strandsagents.com/docs/user-guide/sdk/multi-agent/multi-agent-patterns/index.md).
