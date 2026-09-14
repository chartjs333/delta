import { CapabilityStateView } from "../components/CapabilityStateView";
import type { ResultQuery } from "./result-loader";
import { SourcedResultCard } from "./SourcedResultCard";

export function SourcedResultsPanel({ query }: { readonly query: ResultQuery }) {
  if (
    query.state === "UNAVAILABLE" ||
    query.state === "LOADING" ||
    query.state === "DEGRADED" ||
    query.state === "ACCESS_DENIED"
  ) {
    return (
      <CapabilityStateView
        capability="governance.controller-independence.read"
        state={query.state}
      />
    );
  }
  if (query.state === "UNSUPPORTED") {
    return (
      <div className="capability-state state-unsupported" role="status">
        Unsupported: the advertised source operation is not available.
      </div>
    );
  }
  if (query.state === "ERROR" || query.state === "INVALID") {
    return (
      <div className="capability-state state-error" role="alert">
        {query.state === "INVALID"
          ? "Result rejected: subject or provenance does not match this document."
          : "Result rejected: the source response is malformed."}
      </div>
    );
  }
  if (query.state === "EMPTY") {
    return <div className="empty-state" role="status">No sourced results returned.</div>;
  }
  return (
    <div>
      {query.state === "STALE" ? (
        <div className="capability-state state-stale" role="status">
          Stale sourced data — provenance is shown below.
        </div>
      ) : null}
      <div className="result-list">
        {query.results.map((result, index) => (
          <SourcedResultCard
            key={`${result.resultType}:${result.subject.id}:${index}`}
            result={result}
          />
        ))}
      </div>
    </div>
  );
}
