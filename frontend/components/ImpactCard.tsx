"use client";

import type { ImpactResult } from "@/lib/api";

const LEVEL_COPY: Record<string, { label: string; className: string }> = {
  CRITICAL: { label: "Critical", className: "text-red-400 border-red-400/40 bg-red-400/10" },
  HIGH: { label: "High", className: "text-orange-400 border-orange-400/40 bg-orange-400/10" },
  MEDIUM: { label: "Medium", className: "text-yellow-400 border-yellow-400/40 bg-yellow-400/10" },
  LOW: { label: "Low", className: "text-emerald-400 border-emerald-400/40 bg-emerald-400/10" },
};

export default function ImpactCard({ result }: { result: ImpactResult }) {
  const level = LEVEL_COPY[result.impact_level] || LEVEL_COPY.LOW;
  return (
    <div className="rounded-lg border border-border bg-card p-4">
      <div className="flex items-center justify-between">
        <div>
          <p className="font-mono text-sm text-foreground">{result.changed_function}</p>
          <p className="text-xs text-muted">{result.file_path}</p>
        </div>
        <div className="text-right">
          <p className="text-2xl font-semibold">{result.impact_score}</p>
          <p className="text-xs text-muted">/ 100</p>
        </div>
      </div>
      <div className="mt-3 flex items-center justify-between">
        <span className={`rounded border px-2 py-1 text-xs font-medium ${level.className}`}>{level.label}</span>
        <span className="text-xs text-muted">{result.explanation}</span>
      </div>
      <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
        <div>
          <p className="text-muted">Direct</p>
          <p className="font-mono">{result.direct_impact.length}</p>
        </div>
        <div>
          <p className="text-muted">Transitive</p>
          <p className="font-mono">{result.transitive_impact.length}</p>
        </div>
      </div>
    </div>
  );
}
