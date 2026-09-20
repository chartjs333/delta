import { useEffect, useMemo, useRef, useState } from "react";

import { SchemaSelector } from "../components/SchemaSelector";
import { SourceSummary } from "../components/CapabilityStateView";
import { FriendlyValidationPanel } from "../components/FriendlyValidationPanel";
import { AdvancedJsonView } from "../components/AdvancedJsonView";
import type {
  DocumentEnvelope,
  SchemaDescriptor,
  SourceDescriptor,
  StructuralValidationResult,
  SubjectReference,
} from "../core/contracts";
import { asAdminUiError } from "../core/errors";
import { BrowserFileGateway } from "../data/browser-file-gateway";
import { LocalJsonAdapter } from "../data/local-json-adapter";
import {
  controllerFormStates,
  ControllerRegistryForm,
} from "../modules/controllers/ControllerRegistryForm";
import { ControllerExplorer } from "../modules/controllers/ControllerExplorer";
import { controllersFromDocument } from "../modules/controllers/controller-model";
import { PairwiseReviewStep } from "../modules/controllers/PairwiseReviewStep";
import { ReadinessSummary } from "../modules/controllers/ReadinessSummary";
import { useLiveExecutionRuntime } from "../modules/live-execution/live-execution-context";
import {
  syncPairwiseReviewDrafts,
  type PairwiseReviewDraft,
} from "../modules/controllers/pairwise-review-draft";
import { querySourcedResults, type ResultQuery } from "../results/result-loader";
import { SourcedResultsPanel } from "../results/SourcedResultsPanel";
import { extensionRegistry } from "./registry";

const defaultAdapter = new LocalJsonAdapter(new BrowserFileGateway());
const DEFAULT_ROUTE = "/controllers";

function routeFromLocation(): string {
  const candidate = window.location.hash.replace(/^#/u, "");
  const registered = extensionRegistry.domainModules.some((module) =>
    module.routes.some((route) => route.path === candidate),
  );
  return registered ? candidate : DEFAULT_ROUTE;
}

export interface AppProps {
  readonly adapter?: LocalJsonAdapter;
}

export function App({ adapter = defaultAdapter }: AppProps) {
  const liveExecutionRuntime = useLiveExecutionRuntime();
  const [activeRoute, setActiveRoute] = useState(routeFromLocation);
  const [navigationOpen, setNavigationOpen] = useState(false);
  const [source, setSource] = useState<SourceDescriptor>();
  const [schemas, setSchemas] = useState<readonly SchemaDescriptor[]>([]);
  const [selectedSchema, setSelectedSchema] = useState<SchemaDescriptor>();
  const [document, setDocument] = useState<DocumentEnvelope>();
  const [controllerKeys, setControllerKeys] = useState<readonly string[]>([]);
  const [pairwiseRecords, setPairwiseRecords] = useState<
    readonly PairwiseReviewDraft[]
  >([]);
  const [validation, setValidation] = useState<StructuralValidationResult>();
  const [resultQuery, setResultQuery] = useState<ResultQuery>({
    state: "LOADING",
    results: [],
  });
  const [notice, setNotice] = useState<string>();
  const nextControllerKey = useRef(0);

  function createControllerKey(): string {
    nextControllerKey.current += 1;
    return `controller-draft-${nextControllerKey.current}`;
  }

  useEffect(() => {
    const selectLocationRoute = () => {
      setActiveRoute(routeFromLocation());
      setNavigationOpen(false);
    };
    window.addEventListener("hashchange", selectLocationRoute);
    return () => window.removeEventListener("hashchange", selectLocationRoute);
  }, []);

  useEffect(() => {
    let active = true;
    Promise.all([adapter.describeSource(), adapter.listSchemas()])
      .then(([nextSource, nextSchemas]) => {
        if (!active) return;
        setSource(nextSource);
        setSchemas(nextSchemas);
        setSelectedSchema(nextSchemas[0]);
      })
      .catch((error: unknown) => {
        if (active) setNotice(asAdminUiError(error).message);
      });
    return () => {
      active = false;
    };
  }, [adapter]);

  const resultSubject = useMemo<SubjectReference>(
    () => ({
      type: document?.documentType ?? "local-document",
      id: document?.origin.displayName ?? "no-document-selected",
      sha256: document?.origin.sha256,
    }),
    [document],
  );

  useEffect(() => {
    let active = true;
    querySourcedResults(
      adapter,
      "governance.controller-independence.read",
      resultSubject,
    ).then((query) => {
      if (active) setResultQuery(query);
    });
    return () => {
      active = false;
    };
  }, [adapter, resultSubject]);

  function activateDocument(next: DocumentEnvelope): void {
    setDocument(next);
    setControllerKeys(
      controllersFromDocument(next.value).map(() => createControllerKey()),
    );
    setPairwiseRecords([]);
    setValidation(undefined);
    setNotice(undefined);
  }

  async function openDocument(): Promise<void> {
    try {
      activateDocument(await adapter.openDocument());
      setSource(await adapter.describeSource());
    } catch (error) {
      setNotice(asAdminUiError(error).message);
    }
  }

  function createDocument(): void {
    activateDocument(adapter.createDocument());
  }

  function changeDraft(
    next: DocumentEnvelope,
    nextControllerKeys: readonly string[],
  ): void {
    setDocument(adapter.updateDocumentText(next, next.text));
    setControllerKeys(nextControllerKeys);
    setValidation(undefined);
    setNotice(undefined);
    void adapter.describeSource().then(setSource);
  }

  async function validateDocument(): Promise<void> {
    if (!document || !selectedSchema) return;
    try {
      const result = await adapter.validateStructure(document, selectedSchema);
      setValidation(result);
      setSource(await adapter.describeSource());
    } catch (error) {
      setValidation(undefined);
      setNotice(asAdminUiError(error).message);
    }
  }

  async function exportDocument(): Promise<void> {
    if (!document) return;
    try {
      const receipt = await adapter.exportDocument(
        document,
        document.origin.displayName,
      );
      setNotice(`Downloaded ${receipt.fileName} as a new file.`);
    } catch (error) {
      setNotice(asAdminUiError(error).message);
    }
  }

  const controllers =
    validation?.status === "VALID" && document
      ? controllersFromDocument(document.value)
      : [];
  const controllerDrafts = document
    ? controllerFormStates(document, controllerKeys)
    : [];
  const controllerIdentitySignature = JSON.stringify(
    controllerDrafts.map((controller) => [
      controller.draftControllerKey,
      controller.controllerId ?? null,
    ]),
  );

  useEffect(() => {
    setPairwiseRecords((current) =>
      syncPairwiseReviewDrafts(controllerDrafts, current),
    );
    // The signature intentionally tracks only stable keys and editable IDs.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [controllerIdentitySignature]);
  const activeDomainRoute = extensionRegistry.domainModules
    .flatMap((module) => module.routes)
    .find((route) => route.path === activeRoute);
  const ActiveDomainRoute = activeDomainRoute?.component;

  return (
    <div className="app-shell">
      <header className="topbar">
        <a className="brand" href="#/controllers" aria-label="Delta Admin UI home">
          <span className="brand-mark" aria-hidden="true">Δ</span>
          <span>Delta <strong>Admin</strong></span>
        </a>
        <div className="topbar-actions">
          <button
            aria-controls="primary-sidebar"
            aria-expanded={navigationOpen}
            className="nav-toggle"
            type="button"
            onClick={() => setNavigationOpen((open) => !open)}
          >
            <span aria-hidden="true">☰</span>
            <span>Menu</span>
          </button>
          <div className="boundary-pill">
            {liveExecutionRuntime.mode === "HTTP_LIVE"
              ? "HTTP live · unattested"
              : "Browser-local · offline"}
          </div>
        </div>
      </header>

      <div className="shell-grid">
        <aside
          className={`sidebar${navigationOpen ? " sidebar-open" : ""}`}
          id="primary-sidebar"
        >
          <nav aria-label="Primary navigation">
            <p className="nav-label">Workspace</p>
            {extensionRegistry.navigation.map((item) => (
              <a
                aria-current={activeRoute === item.route ? "page" : undefined}
                href={`#${item.route}`}
                key={item.id}
                onClick={() => {
                  setActiveRoute(item.route);
                  setNavigationOpen(false);
                }}
              >
                <span aria-hidden="true">◫</span> {item.label}
              </a>
            ))}
          </nav>
          {source ? <SourceSummary source={source} /> : <p role="status">Loading source…</p>}
        </aside>

        <main id="workspace">
          {activeRoute === DEFAULT_ROUTE ? (
            <>
          <section className="hero">
            <div>
              <p className="eyebrow">Local document workspace</p>
              <h1>Inspect structure.<br />Keep authority outside the UI.</h1>
              <p>
                Open, edit, validate, and export JSON locally. Nothing here signs,
                authorizes, computes quorum, or changes Delta state.
              </p>
            </div>
            <div className="hero-actions">
              <button className="primary" type="button" onClick={() => void openDocument()}>
                Open JSON
              </button>
              <button type="button" onClick={createDocument}>New document</button>
            </div>
          </section>

          {notice ? <div className="notice" role="status">{notice}</div> : null}

          {!document ? (
            <section className="welcome-card">
              <p className="eyebrow">No document selected</p>
              <h2>Start with a local file or a clean register.</h2>
              <p>
                Files remain in this browser session. The original is never
                overwritten, and no URL is fetched automatically.
              </p>
            </section>
          ) : (
            <>
              <section className="document-bar" aria-label="Open document">
                <div>
                  <span>Local draft</span>
                  <strong>{document.origin.displayName}</strong>
                </div>
                <div className="document-actions">
                  <button
                    type="button"
                    disabled={!document || !selectedSchema}
                    onClick={() => void validateDocument()}
                  >
                    Validate structure
                  </button>
                  <button
                    className="primary"
                    type="button"
                    disabled={!document}
                    onClick={() => void exportDocument()}
                  >
                    Download new file
                  </button>
                </div>
              </section>

              <div className="workspace-grid">
                {document ? (
                  <ControllerRegistryForm
                    draft={document}
                    controllerKeys={controllerKeys}
                    createControllerKey={createControllerKey}
                    onChange={changeDraft}
                  />
                ) : null}
                <SchemaSelector
                  schemas={schemas}
                  selected={selectedSchema}
                  onSelect={(schema) => {
                    setSelectedSchema(schema);
                    setValidation(undefined);
                  }}
                />
              </div>

              {document ? <AdvancedJsonView draft={document} /> : null}

              <ReadinessSummary
                controllers={controllerDrafts}
                records={pairwiseRecords}
                validation={validation}
                resultQuery={resultQuery}
              />

              <PairwiseReviewStep
                controllers={controllerDrafts}
                records={pairwiseRecords}
                onChange={setPairwiseRecords}
              />

              {validation ? <FriendlyValidationPanel result={validation} /> : null}
              {validation?.status === "VALID" ? (
                <ControllerExplorer controllers={controllers} />
              ) : null}
            </>
          )}

          <section className="results-section" aria-labelledby="results-heading">
            <div className="section-heading">
              <div>
                <p className="eyebrow">External authority only</p>
                <h2 id="results-heading">Independence assessment</h2>
              </div>
            </div>
            <SourcedResultsPanel query={resultQuery} />
          </section>
            </>
          ) : ActiveDomainRoute ? (
            <div className="extension-route">
              <ActiveDomainRoute />
            </div>
          ) : (
            <div className="capability-state state-error" role="alert">
              Registered route unavailable.
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
