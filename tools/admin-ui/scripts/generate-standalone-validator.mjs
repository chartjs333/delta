import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";

import Ajv2020 from "ajv/dist/2020.js";
import standaloneCode from "ajv/dist/standalone/index.js";

const schemaUrl = new URL("../src/schemas/controller-register.schema.json", import.meta.url);
const outputUrl = new URL(
  "../src/validation/generated/controller-register-validator.mjs",
  import.meta.url,
);
const schema = JSON.parse(await readFile(schemaUrl, "utf8"));
const ajv = new Ajv2020({
  allErrors: true,
  strict: true,
  validateFormats: false,
  code: { source: true, esm: true },
});
ajv.addSchema(schema);
const generated = `${standaloneCode(ajv, {
  validateControllerRegister: schema.$id,
})}\n`;

if (process.argv.includes("--check")) {
  const existing = await readFile(outputUrl, "utf8").catch(() => "");
  if (existing !== generated) {
    process.stderr.write(
      `${fileURLToPath(outputUrl)} is stale; run npm run generate:validators.\n`,
    );
    process.exitCode = 1;
  }
} else {
  await writeFile(outputUrl, generated, "utf8");
}
