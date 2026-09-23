import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { GuidedRun } from "./GuidedRun";
import { ProtocolGuide } from "./ProtocolGuide";
import { setLanguage, useLanguage } from "../../i18n";
import type {
  LiveExecutionPort,
  LiveExecutionStatus,
  LiveExecutionReceipt,
} from "./live-execution-port";
import {
  createDefaultIntentDraft,
} from "./intent-builder";

const id = "55555555-5555-4555-8555-555555555555";
const result = (state: LiveExecutionStatus["state"]): LiveExecutionStatus => ({
  statusId: id,
  state,
  operation: "TRAIN_TICKET",
  updatedAt: "2026-09-23T20:00:00Z",
  terminal: ["COMPLETED", "FAILED"].includes(state),
  authority: "CONTROLLER_HTTP_STATUS",
  trustBadge: "UNATTESTED_CONTROLLER_STATUS",
  summary: state,
  lineage: { executionId: id },
});
const receipt: LiveExecutionReceipt = {
  schema_version: "1.0.0",
  receipt_type: "DELTAREDUCE_EXECUTION_RECEIPT",
  execution: { terminal_status: "COMPLETED", verdict: "SUCCESS" },
  workload: {
    model_plugin_id: "tabular-10gene-phenotype-v1",
    dataset_id: "synthetic-10gene-cohort-v1",
    executed_scope: "PLUGIN_BOUNDARY",
    workload_config_digest: "sha256:test",
  },
  provenance: {
    repository: "test",
    backend_commit: "test",
    produced_at: "2026-09-23T20:00:00Z",
    intent_id: "intent",
    intent_digest: "sha256:intent",
    admission_id: "admission",
    admission_digest: "sha256:admission",
    execution_id: id,
  },
};
function port(): LiveExecutionPort {
  return {
    describeLiveSource: vi.fn(),
    previewDraft: vi.fn(),
    listStatuses: vi.fn(),
    submitIntent: vi.fn(async () => result("QUEUED")),
    getStatus: vi.fn(async () => result("COMPLETED")),
    getReceipt: vi.fn(async () => receipt),
  };
}
function View({ adapter }: { adapter: LiveExecutionPort }) {
  useLanguage();
  return <GuidedRun port={adapter} enabled onStatus={() => {}} />;
}
afterEach(() => {
  vi.useRealTimers();
  act(() => setLanguage("en"));
});

describe("guided local execution", () => {
  it("submits once through the existing intent contract, follows status and gates the download on a verified receipt", async () => {
    vi.useFakeTimers();
    const adapter = port();
    render(<View adapter={adapter} />);
    fireEvent.change(screen.getByLabelText("Run name"), {
      target: { value: "demo_42" },
    });
    const start = screen.getByRole("button", { name: "Start training" });
    await act(async () => {
      fireEvent.click(start);
      fireEvent.click(start);
    });
    expect(adapter.submitIntent).toHaveBeenCalledTimes(1);
    const submitted = vi.mocked(adapter.submitIntent).mock.calls[0][0] as {
      operation_payload: unknown;
      workload: unknown;
    };
    expect(submitted.operation_payload).toEqual({
      ticket_id: "demo_42",
      partition_id: "partition_00",
    });
    expect(submitted.workload).toEqual(createDefaultIntentDraft().workload);
    expect(
      screen.queryByRole("button", { name: "Download receipt" }),
    ).toBeNull();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(1000);
    });
    expect(adapter.getReceipt).toHaveBeenCalledWith(id);
    expect(screen.getByRole("heading", { name: "Result ready" })).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Download receipt" }),
    ).toBeTruthy();
  });
  it("keeps the submitted request and result intact across language changes", async () => {
    const adapter = port();
    vi.mocked(adapter.submitIntent).mockResolvedValue(result("COMPLETED"));
    render(<View adapter={adapter} />);
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Start training" }));
    });
    const original = JSON.stringify(
      vi.mocked(adapter.submitIntent).mock.calls[0][0],
    );
    act(() => setLanguage("ru"));
    expect(
      screen.getByRole("heading", { name: "Результат готов" }),
    ).toBeTruthy();
    expect(
      screen.getByRole("button", { name: "Скачать receipt" }),
    ).toBeTruthy();
    expect(
      JSON.stringify(vi.mocked(adapter.submitIntent).mock.calls[0][0]),
    ).toBe(original);
    expect(adapter.submitIntent).toHaveBeenCalledTimes(1);
  });
  it("does not report a verified result when receipt validation fails, and retries reads without resubmitting", async () => {
    const adapter = port();
    vi.mocked(adapter.submitIntent).mockResolvedValue(result("COMPLETED"));
    vi.mocked(adapter.getReceipt!).mockRejectedValueOnce(
      new Error("Receipt digest mismatch"),
    );
    render(<View adapter={adapter} />);
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Start training" }));
    });
    expect(screen.getByRole("alert").textContent).toContain(
      "Unable to confirm",
    );
    expect(
      screen.queryByRole("button", { name: "Download receipt" }),
    ).toBeNull();
    await act(async () => {
      fireEvent.click(
        screen.getByRole("button", { name: "Check status again" }),
      );
    });
    expect(
      screen.getByRole("button", { name: "Download receipt" }),
    ).toBeTruthy();
    expect(adapter.submitIntent).toHaveBeenCalledTimes(1);
  });
  it("blocks another submission after uncertain admission and shows no success", async () => {
    const adapter = port();
    vi.mocked(adapter.submitIntent).mockRejectedValue(
      new Error("Connection lost"),
    );
    render(<View adapter={adapter} />);
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Start training" }));
    });
    expect(screen.getByRole("alert").textContent).toContain(
      "Admission is uncertain",
    );
    expect(
      screen
        .getByRole("button", { name: "Start training" })
        .hasAttribute("disabled"),
    ).toBe(true);
    expect(
      screen.queryByRole("button", { name: "Download receipt" }),
    ).toBeNull();
  });
  it("never loads a receipt for a failed run", async () => {
    const adapter = port();
    vi.mocked(adapter.submitIntent).mockResolvedValue(result("FAILED"));
    render(<View adapter={adapter} />);
    await act(async () => {
      fireEvent.click(screen.getByRole("button", { name: "Start training" }));
    });
    expect(
      screen.getByRole("heading", { name: "Execution failed" }),
    ).toBeTruthy();
    expect(adapter.getReceipt).not.toHaveBeenCalled();
    expect(
      screen.queryByRole("button", { name: "Download receipt" }),
    ).toBeNull();
  });
  it("does not poll after unmount or act on a late submission response", async () => {
    vi.useFakeTimers();
    const adapter = port();
    let resolve!: (s: LiveExecutionStatus) => void;
    vi.mocked(adapter.submitIntent).mockReturnValue(
      new Promise((done) => {
        resolve = done;
      }),
    );
    const view = render(<View adapter={adapter} />);
    fireEvent.click(screen.getByRole("button", { name: "Start training" }));
    view.unmount();
    await act(async () => {
      resolve(result("QUEUED"));
      await vi.advanceTimersByTimeAsync(2000);
    });
    expect(adapter.getStatus).not.toHaveBeenCalled();
  });
  it("keeps the protocol illustration informational and traversable", () => {
    render(<ProtocolGuide />);
    fireEvent.click(screen.getByText("How DeltaReduce works"));
    fireEvent.click(screen.getByRole("button", { name: /5\. Aggregation:/ }));
    expect(screen.getByText(/Exact integer shard results/)).toBeTruthy();
    expect(
      screen.getByText(/These are not live progress indicators/),
    ).toBeTruthy();
  });
});
