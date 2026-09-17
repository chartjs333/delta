import type { JsonValue } from "../../core/contracts";

export type ControllerRecord = Readonly<Record<string, JsonValue>>;

function asRecord(value: JsonValue): ControllerRecord | undefined {
  return value !== null && typeof value === "object" && !Array.isArray(value)
    ? (value as ControllerRecord)
    : undefined;
}

export function controllersFromDocument(value: JsonValue): readonly ControllerRecord[] {
  const root = asRecord(value);
  const controllers = root?.controllers;
  if (!Array.isArray(controllers)) {
    return [];
  }
  return controllers.flatMap((controller) => {
    const record = asRecord(controller);
    return record ? [record] : [];
  });
}

export function controllerLabel(
  controller: ControllerRecord,
  index: number,
): string {
  const controllerId = controller.controller_id;
  if (typeof controllerId === "string" && controllerId.trim()) {
    return controllerId;
  }
  const displayLabel = controller.display_label;
  if (typeof displayLabel === "string" && displayLabel.trim()) {
    return displayLabel;
  }
  return `Controller ${index + 1}`;
}
