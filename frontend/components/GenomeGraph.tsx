"use client";

import { useCallback, useEffect, useMemo } from "react";
import ReactFlow, {
  type Node,
  type Edge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
} from "reactflow";
import "reactflow/dist/style.css";

import type { ImpactResult } from "@/lib/api";

const COLORS: Record<string, { bg: string; border: string; text: string }> = {
  repository: { bg: "#1e293b", border: "#334155", text: "#e2e8f0" },
  module: { bg: "#0f172a", border: "#1d4ed8", text: "#93c5fd" },
  class: { bg: "#1e1b4b", border: "#6d28d9", text: "#c4b5fd" },
  function: { bg: "#052e16", border: "#16a34a", text: "#86efac" },
  method: { bg: "#431407", border: "#ea580c", text: "#fdba74" },
  import: { bg: "#1c1917", border: "#57534e", text: "#d6d3d1" },
};

function severityColor(level: string) {
  switch (level) {
    case "CRITICAL":
      return "#ef4444";
    case "HIGH":
      return "#f97316";
    case "MEDIUM":
      return "#f59e0b";
    case "LOW":
      return "#10b981";
    default:
      return "#64748b";
  }
}

function getNodeType(type: string) {
  return type?.toLowerCase() || "function";
}

function hashString(str: string): number {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    const char = str.charCodeAt(i);
    hash = ((hash << 5) - hash) + char;
    hash |= 0;
  }
  return Math.abs(hash);
}

function deterministicPosition(id: string): { x: number; y: number } {
  const h = hashString(id);
  return {
    x: (h % 500) + 50,
    y: ((h >> 5) % 400) + 50,
  };
}

export default function GenomeGraph({ analysisId, impacts }: { analysisId: string; impacts: ImpactResult[] }) {
  const initialNodes = useMemo(() => {
    if (!impacts?.length) return [];
    const seen = new Map<string, Node>();
    for (const impact of impacts) {
      for (const raw of impact.nodes) {
        const id = String(raw.id ?? raw.qualified_name ?? raw.name);
        if (seen.has(id)) continue;
        const type = getNodeType(String(raw.type ?? ""));
        const palette = COLORS[type] || COLORS.function;
        const label = String(raw.name ?? id);
        const impactForNode = impact.affected_components?.includes(type === "module" ? label : label.split(".")[0])
          ? severityColor(impact.impact_level)
          : undefined;

        seen.set(id, {
          id,
          type: "default",
          position: deterministicPosition(id),
          data: {
            label,
            type,
            file: String(raw.file_path ?? ""),
            line: Number(raw.lineno ?? 0),
            callers: impact.direct_impact ?? [],
            callees: impact.transitive_impact ?? [],
            downstream: impact.transitive_impact ?? [],
          },
          style: {
            background: palette.bg,
            color: palette.text,
            border: `1px solid ${impactForNode || palette.border}`,
            padding: 8,
            borderRadius: 8,
            fontSize: 12,
            fontFamily: "var(--font-geist-mono)",
            minWidth: 140,
          },
        });
      }
    }
    return Array.from(seen.values());
  }, [impacts]);

  const initialEdges = useMemo(() => {
    if (!impacts?.length) return [];
    const seen = new Map<string, Edge>();
    for (const impact of impacts) {
      for (const raw of impact.edges) {
        const source = String(raw.source ?? "");
        const target = String(raw.target ?? "");
        const key = `${source}->${target}`;
        if (!source || !target || seen.has(key)) continue;
        seen.set(key, {
          id: key,
          source,
          target,
          type: "smoothstep",
          animated: false,
          markerEnd: { type: MarkerType.ArrowClosed, color: "#64748b" },
          style: { stroke: "#475569", strokeWidth: 1.5 },
        });
      }
    }
    return Array.from(seen.values());
  }, [impacts]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  useEffect(() => {
    setNodes(initialNodes);
    setEdges(initialEdges);
  }, [analysisId, initialNodes, initialEdges, setNodes, setEdges]);

  const onNodeClick = useCallback(
    (_: React.MouseEvent, node: Node) => {
      const data = node.data as Record<string, unknown>;
      const details = [
        `File: ${data.file ?? "unknown"}`,
        `Line: ${data.line ?? 0}`,
        `Callers: ${(data.callers as string[] | undefined)?.slice(0, 5).join(", ") || "none"}`,
        `Callees: ${(data.callees as string[] | undefined)?.slice(0, 5).join(", ") || "none"}`,
        `Downstream: ${(data.downstream as string[] | undefined)?.length ?? 0} components`,
      ];
      alert(details.join("\n"));
    },
    []
  );

  return (
    <div className="h-[520px] w-full rounded-lg border border-border bg-card">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        fitView
        attributionPosition="bottom-left"
        defaultEdgeOptions={{
          type: "smoothstep",
          markerEnd: { type: MarkerType.ArrowClosed, color: "#64748b" },
        }}
      >
        <Background color="#1f2937" gap={16} />
        <Controls />
        <MiniMap nodeColor={(n) => (n.style?.color as string) || "#3b82f6"} maskColor="#0a0a0f" />
      </ReactFlow>
    </div>
  );
}
