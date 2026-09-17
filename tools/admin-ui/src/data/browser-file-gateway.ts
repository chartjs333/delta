import { AdminUiError } from "../core/errors";

export interface SelectedLocalFile {
  readonly name: string;
  readonly bytes: Uint8Array;
}

export interface LocalFileGateway {
  selectJsonFile(): Promise<SelectedLocalFile>;
  downloadNewFile(bytes: Uint8Array, suggestedName: string): Promise<void>;
}

export class BrowserFileGateway implements LocalFileGateway {
  async selectJsonFile(): Promise<SelectedLocalFile> {
    const input = document.createElement("input");
    input.type = "file";
    input.accept = ".json,application/json";
    input.multiple = false;

    const file = await new Promise<File>((resolve, reject) => {
      input.addEventListener(
        "change",
        () => {
          const selected = input.files?.item(0);
          if (selected) {
            resolve(selected);
          } else {
            reject(
              new AdminUiError(
                "VALIDATION_CANCELLED",
                "No local JSON file was selected.",
              ),
            );
          }
        },
        { once: true },
      );
      input.addEventListener(
        "cancel",
        () =>
          reject(
            new AdminUiError(
              "VALIDATION_CANCELLED",
              "Local file selection was cancelled.",
            ),
          ),
        { once: true },
      );
      input.click();
    });

    return {
      name: file.name,
      bytes: new Uint8Array(await file.arrayBuffer()),
    };
  }

  async downloadNewFile(bytes: Uint8Array, suggestedName: string): Promise<void> {
    const copy = new Uint8Array(bytes.byteLength);
    copy.set(bytes);
    const blob = new Blob([copy.buffer], {
      type: "application/json;charset=utf-8",
    });
    const objectUrl = URL.createObjectURL(blob);
    try {
      const anchor = document.createElement("a");
      anchor.download = suggestedName;
      anchor.href = objectUrl;
      anchor.rel = "noopener";
      anchor.click();
    } finally {
      URL.revokeObjectURL(objectUrl);
    }
  }
}
