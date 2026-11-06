import { AgentCoreApplication, type AgentCoreApplicationProps } from '@aws/agentcore-cdk';
import { Stack, type StackProps } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as fs from 'fs';
import * as path from 'path';

export interface AgentCoreStackProps extends StackProps {
  /** Props for the AgentCore application, produced by transformAgentCoreJson from agentcore/agentcore.json. */
  application: AgentCoreApplicationProps;
}

/**
 * The stack the AgentCore CLI deploys. Everything declared in agentcore/agentcore.json is
 * created by the AgentCoreApplication construct. Add your own resources below it and wire
 * them to your runtimes and harnesses through the application's accessors.
 */
export class AgentCoreStack extends Stack {
  public readonly application: AgentCoreApplication;

  constructor(scope: Construct, id: string, props: AgentCoreStackProps) {
    super(scope, id, props);
    this.application = new AgentCoreApplication(this, 'Application', props.application);

    // Il Runtime può usare Code Interpreter e Browser gestiti da AWS.
    // Il controllo evita errori quando il Runtime non c'è più (per esempio durante la pulizia).
    if (props.application.spec.runtimes?.some((r) => r.name === 'agent')) {
      const agent = this.application.runtime('agent');
      agent.grant(
        [
          'bedrock-agentcore:StartCodeInterpreterSession',
          'bedrock-agentcore:StopCodeInterpreterSession',
          'bedrock-agentcore:GetCodeInterpreterSession',
          'bedrock-agentcore:InvokeCodeInterpreter',
        ],
        [`arn:${this.partition}:bedrock-agentcore:${this.region}:aws:code-interpreter/*`],
      );
      agent.grant(
        [
          'bedrock-agentcore:StartBrowserSession',
          'bedrock-agentcore:StopBrowserSession',
          'bedrock-agentcore:GetBrowserSession',
          'bedrock-agentcore:ConnectBrowserAutomationStream',
        ],
        [`arn:${this.partition}:bedrock-agentcore:${this.region}:aws:browser/*`],
      );

      // Lab 8: se esiste guardrail.json nella cartella del progetto, il Runtime usa quel guardrail.
      const fileGuardrail = path.resolve(process.cwd(), '..', '..', 'guardrail.json');
      if (fs.existsSync(fileGuardrail)) {
        const guardrail = JSON.parse(fs.readFileSync(fileGuardrail, 'utf8'));
        agent.addEnvironmentVariable('GUARDRAIL_ID', guardrail.id);
        agent.addEnvironmentVariable('GUARDRAIL_VERSIONE', String(guardrail.versione));
        agent.grant(
          ['bedrock:ApplyGuardrail'],
          [`arn:${this.partition}:bedrock:${this.region}:${this.account}:guardrail/${guardrail.id}`],
        );
      }
    }

    // Example: give a runtime a DynamoDB table.
    //
    // import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
    // const orders = new dynamodb.Table(this, 'Orders', {
    //   partitionKey: { name: 'pk', type: dynamodb.AttributeType.STRING },
    // });
    // const checkout = this.application.runtime('checkout'); // or .harness('support')
    // checkout.grantReadWrite(orders);
    // checkout.addEnvironmentVariable('ORDERS_TABLE', orders.tableName);
  }
}
