import type { BatchRunStatus } from "../../types/contracts";

const STATUS_CLASS: Record<BatchRunStatus, string> = {
  pending: "badge badge-pending",
  running: "badge badge-running",
  completed: "badge badge-completed",
  failed: "badge badge-failed",
  partial: "badge badge-partial",
};

export function StatusBadge({ status }: { status: BatchRunStatus | string }) {
  const key = status as BatchRunStatus;
  const className = STATUS_CLASS[key] ?? "badge";
  return <span className={className}>{status}</span>;
}
