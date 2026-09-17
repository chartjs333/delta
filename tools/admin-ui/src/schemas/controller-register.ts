import type { SchemaDescriptor } from "../core/contracts";
import controllerRegisterSchemaText from "./controller-register.schema.json?raw";

export const CONTROLLER_REGISTER_SCHEMA = Object.freeze({
  schemaId: "urn:deltareduce:admin-ui:local:controller-governance-register-v1",
  version: "1.0.0",
  authorityClass: "LOCAL_FIXTURE",
  documentType: "CONTROLLER_GOVERNANCE_REGISTER",
  source: {
    kind: "BUNDLED_FIXTURE",
    repository: "chartjs333/delta",
    path: "tools/admin-ui/src/schemas/controller-register.schema.json",
    sha256: "d464909ccc7735307d0e715ac4ee54b31a84b0c6b70d737410aa152885acc28c",
  },
} satisfies SchemaDescriptor);

export { controllerRegisterSchemaText };
