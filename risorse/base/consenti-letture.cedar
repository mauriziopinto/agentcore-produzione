// Consente sempre gli strumenti che leggono dati o aprono un ticket.
permit (
    principal,
    action in [
        AgentCore::Action::"crm___get_cliente",
        AgentCore::Action::"crm___get_fatture",
        AgentCore::Action::"crm___apri_ticket"
    ],
    resource == AgentCore::Gateway::"GATEWAY_ARN"
);
