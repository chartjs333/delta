// @vitest-environment node

import type {
  DocumentEnvelope,
  JsonValue,
  SchemaEnvelope,
} from "../core/contracts";
import type {
  LocalFileGateway,
  SelectedLocalFile,
} from "../data/browser-file-gateway";
import {
  CONTROLLER_REGISTER_SCHEMA,
  LocalJsonAdapter,
} from "../data/local-json-adapter";
import schemaText from "../schemas/controller-register.schema.json?raw";
import { runDataSourcePortContract } from "./data-source-port.contract";
import { InMemoryDataSourceAdapter } from "./in-memory-data-source-adapter";

const contractText = `${JSON.stringify({
  document_type: "CONTROLLER_GOVERNANCE_REGISTER",
  document_version: "1.0.0",
  controllers: [{ controller_id: "contract-controller", future_field: true }],
}, null, 2)}\n`;
const contractBytes = new TextEncoder().encode(contractText);

class ContractFileGateway implements LocalFileGateway {
  constructor(private readonly source: SelectedLocalFile) {}

  async selectJsonFile(): Promise<SelectedLocalFile> {
    return { ...this.source, bytes: this.source.bytes.slice() };
  }

  async downloadNewFile(_bytes: Uint8Array, _suggestedName: string): Promise<void> {
    // Contract invocation is the explicit user-triggered export boundary.
  }
}

const memoryDocument: DocumentEnvelope = {
  text: contractText,
  value: JSON.parse(contractText) as JsonValue,
  documentType: "CONTROLLER_GOVERNANCE_REGISTER",
  authorityClass: "LOCAL_DRAFT",
  origin: {
    kind: "BUNDLED_FIXTURE",
    displayName: "contract-register.json",
    byteLength: contractBytes.byteLength,
  },
};
const memorySchema: SchemaEnvelope = {
  descriptor: CONTROLLER_REGISTER_SCHEMA,
  text: schemaText,
  value: JSON.parse(schemaText) as JsonValue,
};

runDataSourcePortContract(
  "LocalJsonAdapter",
  () =>
    new LocalJsonAdapter(
      new ContractFileGateway({
        name: "contract-register.json",
        bytes: contractBytes,
      }),
    ),
);

runDataSourcePortContract(
  "InMemoryDataSourceAdapter",
  () =>
    new InMemoryDataSourceAdapter({
      document: memoryDocument,
      schema: memorySchema,
    }),
);
