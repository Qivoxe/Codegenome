"use client";

import { useEffect, useMemo, useState } from "react";
import { GitBranch, Play, RefreshCw } from "lucide-react";
import GenomeGraph from "@/components/GenomeGraph";
import ImpactCard from "@/components/ImpactCard";
import {
  getGraphData,
  getImpactResults,
  listRepositories,
  runAnalysis,
  type GraphData,
  type ImpactResult,
  type Repository,
} from "@/lib/api";

export default function Dashboard() {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<Repository | null>(null);
  const [analysis, setAnalysis] = useState<{ id: string } | null>(null);
  const [impacts, setImpacts] = useState<ImpactResult[]>([]);
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    listRepositories().then(setRepositories).catch(console.error);
  }, []);

  const aggregateScore = useMemo(() => {
    if (!impacts.length) return 0;
    return Math.round(impacts.reduce((sum, i) => sum + i.impact_score, 0) / impacts.length);
  }, [impacts]);

  const aggregateLevel = useMemo(() => {
    if (!impacts.length) return "LOW";
    const counts = new Map<string, number>();
    for (const i of impacts) counts.set(i.impact_level, (counts.get(i.impact_level) || 0) + 1);
    const order = ["LOW", "MEDIUM", "HIGH", "CRITICAL"];
    return order.reduce((a, b) => (counts.get(a)! > counts.get(b)! ? a : b));
  }, [impacts]);

  const allComponents = useMemo(() => {
    const map = new Map<string, { level: string; name: string }>();
    for (const i of impacts) {
      for (const comp of i.affected_components) {
        const existing = map.get(comp);
        if (!existing || ["CRITICAL", "HIGH", "MEDIUM", "LOW"].indexOf(i.impact_level) < ["CRITICAL", "HIGH", "MEDIUM", "LOW"].indexOf(existing.level)) {
          map.set(comp, { level: i.impact_level, name: comp });
        }
      }
    }
    return Array.from(map.values()).sort((a, b) => a.name.localeCompare(b.name));
  }, [impacts]);

  const handleAnalyze = async () => {
    if (!selectedRepo) return;
    setLoading(true);
    try {
      const run = await runAnalysis(selectedRepo.id);
      setAnalysis({ id: run.id });
      const [impactResults, graphData] = await Promise.all([
        getImpactResults(run.id),
        getGraphData(run.id),
      ]);
      setImpacts(impactResults);
      setGraph(graphData);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <GitBranch className="h-5 w-5 text-accent" />
            <h1 className="text-lg font-semibold">CodeGenome</h1>
          </div>
          <span className="text-xs text-muted">Phase 2 • Local Platform</span>
        </div>
      </header>

      <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-8">
        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          <div className="lg:col-span-4 space-y-4">
            <div className="rounded-lg border border-border bg-card p-4">
              <h2 className="text-sm font-medium text-muted">Repository</h2>
              <div className="mt-3 flex flex-col gap-2">
                <select
                  value={selectedRepo?.id || ""}
                  onChange={(e) => setSelectedRepo(repositories.find((r) => r.id === e.target.value) || null)}
                  className="h-10 rounded-md border border-border bg-background px-3 text-sm focus:outline-none focus:ring-1 focus:ring-accent"
                >
                  <option value="">Select repository</option>
                  {repositories.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.name}
                    </option>
                  ))}
                </select>
                <button
                  onClick={handleAnalyze}
                  disabled={!selectedRepo || loading}
                  className="inline-flex items-center justify-center gap-2 rounded-md bg-accent px-4 py-2 text-sm font-medium text-white hover:bg-blue-600 disabled:opacity-50"
                >
                  {loading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                  {loading ? "Analyzing..." : "Analyze"}
                </button>
              </div>
            </div>

            {analysis && (
              <div className="rounded-lg border border-border bg-card p-4">
                <h2 className="text-sm font-medium text-muted">Impact Score</h2>
                <div className="mt-3 flex items-end justify-between">
                  <div>
                    <span className="text-4xl font-semibold">{aggregateScore}</span>
                    <span className="text-sm text-muted">/ 100</span>
                  </div>
                  <span className="rounded border px-2 py-1 text-xs font-medium">{aggregateLevel}</span>
                </div>
              </div>
            )}

            {allComponents.length > 0 && (
              <div className="rounded-lg border border-border bg-card p-4">
                <h2 className="text-sm font-medium text-muted">Affected Components</h2>
                <div className="mt-3 flex flex-col gap-2">
                  {allComponents.map((comp) => (
                    <div key={comp.name} className="flex items-center justify-between rounded border border-border bg-background px-3 py-2">
                      <span className="font-mono text-xs">{comp.name}</span>
                      <span className="text-xs">{comp.level}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {impacts.length > 0 && (
              <div className="rounded-lg border border-border bg-card p-4">
                <h2 className="text-sm font-medium text-muted">Changed Function</h2>
                {impacts.map((i) => (
                  <p key={i.id} className="mt-2 font-mono text-sm">
                    {i.changed_function}
                  </p>
                ))}
              </div>
            )}
          </div>

          <div className="lg:col-span-8 space-y-4">
            {analysis && (
              <div className="rounded-lg border border-border bg-card p-4">
                <h2 className="text-sm font-medium text-muted">Impact Graph</h2>
                {graph ? (
                  <GenomeGraph analysisId={analysis.id} impacts={impacts} />
                ) : (
                  <p className="mt-4 text-xs text-muted">Graph data not available</p>
                )}
              </div>
            )}

            {impacts.length > 0 && (
              <div className="space-y-3">
                <h2 className="text-sm font-medium text-muted">Impact Results</h2>
                {impacts.map((i) => (
                  <ImpactCard key={i.id} result={i} />
                ))}
              </div>
            )}

            {impacts.length > 0 && (
              <div className="rounded-lg border border-border bg-card p-4">
                <h2 className="text-sm font-medium text-muted">Impact Paths</h2>
                <div className="mt-3 flex flex-col gap-2">
                  {impacts.flatMap((i) =>
                    (i.impact_paths || []).slice(0, 3).map((path, idx) => (
                      <div key={`${i.id}-${idx}`} className="font-mono text-xs text-muted">
                        {path.join(" → ")}
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
