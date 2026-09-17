declare module "*generate-catalog-snapshot.mjs" {
  export function generateCatalogSnapshot(options?: {
    registryRoot?: string;
    targetSnapshotPath?: string;
    backendRef?: string;
  }): Promise<string>;

  export function validateGeneratedSnapshot(snapshot: unknown): any;

  export function writeCatalogSnapshotAtomically(
    targetPath: string,
    content: string
  ): Promise<void>;
}
