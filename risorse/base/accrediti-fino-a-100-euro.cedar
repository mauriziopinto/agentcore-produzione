// Tetto massimo: nessun accredito sopra i 100 euro passa dal Gateway,
// qualunque cosa decida l'agente e chiunque lo approvi.
permit (
    principal,
    action == AgentCore::Action::"crm___emetti_accredito",
    resource == AgentCore::Gateway::"GATEWAY_ARN"
)
when {
    context.input.importo_euro <= 100
};
