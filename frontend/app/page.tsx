"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { GitBranch, Play, RefreshCw, Search, AlertCircle } from "lucide-react";
import GenomeGraph from "@/components/GenomeGraph";
import ImpactCard from "@/components/ImpactCard";
import {
  analyzeFunctionImpact,
  getAnalysisFunctions,
  getAnalysisStatus,
  getGraphData,
  getImpactResults,
  listRepositories,
  registerGitHubRepo,
  runAnalysis,
  type AnalysisStatus,
  type FunctionInfo,
  type GraphData,
  type ImpactAnalysisResponse,
  type ImpactResult,
  type Repository,
} from "@/lib/api";

type Screen = "input" | "analyzing" | "results";

export default function Dashboard() {
  const [screen, setScreen] = useState<Screen>("input");
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [selectedRepo, setSelectedRepo] = useState<Repository | null>(null);
  const [analysis, setAnalysis] = useState<{ id: string } | null>(null);
  const [status, setStatus] = useState<AnalysisStatus | null>(null);
  const [functions, setFunctions] = useState<FunctionInfo[]>([]);
  const [impacts, setImpacts] = useState<ImpactResult[]>([]);
  const [graph, setGraph] = useState<GraphData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [githubUrl, setGithubUrl] = useState("");
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedFunction, setSelectedFunction] = useState<FunctionInfo | null>(null);
  const [impactResult, setImpactResult] = useState<ImpactAnalysisResponse | null>(null);

  useEffect(() => {
    listRepositories().then(setRepositories).catch(console.error);
  }, []);

  useEffect(() => {
    if (!analysis?.id || screen !== "analyzing") return;
    const interval = setInterval(async () => {
      try {
        const s = await getAnalysisStatus(analysis.id);
        setStatus(s);
        if (s.status === "completed") {
          clearInterval(interval);
          const [impactResults, graphData, funcs] = await Promise.all([
            getImpactResults(analysis.id),
            getGraphData(analysis.id),
            getAnalysisFunctions(analysis.id),
          ]);
          setImpacts(impactResults);
          setGraph(graphData);
          setFunctions(funcs);
          setScreen("results");
          setLoading(false);
        } else if (s.status === "failed") {
          clearInterval(interval);
          setError(s.message || "Analysis failed");
          setLoading(false);
        }
      } catch (err) {
        console.error(err);
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [analysis?.id, screen]);

  const handleGitHubSubmit = async () => {
    setError(null);
    setLoading(true);
    try {
      const repo = await registerGitHubRepo(githubUrl.trim());
      setSelectedRepo(repo);
      const analysisRun = await runAnalysis(repo.id);
      setAnalysis({ id: analysisRun.id });
      setStatus({
        analysis_id: analysisRun.id,
        status: analysisRun.status,
        stage: analysisRun.stage,
        progress: analysisRun.progress,
        message: analysisRun.message,
      });
      setScreen("analyzing");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to analyze repository";
      setError(message);
      setLoading(false);
    }
  };

  const handleAnalyzeImpact = async () => {
    if (!analysis?.id || !selectedFunction) return;
    try {
      const result = await analyzeFunctionImpact(analysis.id, selectedFunction.id);
      setImpactResult(result);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to analyze impact";
      setError(message);
    }
  };

  const filteredFunctions = useMemo(() => {
    if (!searchQuery.trim()) return functions.slice(0, 50);
    const q = searchQuery.toLowerCase();
    return functions.filter((f) => f.qualified_name.toLowerCase().includes(q)).slice(0, 50);
  }, [functions, searchQuery]);

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

  if (screen === "input") {
    return (
      <div className="flex min-h-screen flex-col">
        <header className="border-b border-border bg-card">
          <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
            <div className="flex items-center gap-3">
              <GitBranch className="h-5 w-5 text-accent" />
              <h1 className="text-lg font-semibold">CodeGenome</h1>
            </div>
            <span className="text-xs text-muted">Software Impact Intelligence</span>
          </div>
        </header>
        <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col items-center justify-center px-6 py-16">
          <h2 className="mb-2 text-center text-3xl font-semibold">Know what your code change could break.</h2>
          <p className="mb-8 text-center text-muted">Paste a public GitHub repository URL to analyze its Software Genome.</p>
          <div className="w-full space-y-4">
            <input
              type="text"
              value={githubUrl}
              onChange={(e) => setGithubUrl(e.target.value)}
              placeholder="https://github.com/owner/repository"
              className="h-12 w-full rounded-md border border-border bg-background px-4 text-sm focus:outline-none focus:ring-1 focus:ring-accent"
              onKeyDown={(e) => e.key === "Enter" && handleGitHubSubmit()}
            />
            <button
              onClick={handleGitHubSubmit}
              disabled={!githubUrl.trim() || loading}
              className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-accent px-4 py-3 text-sm font-medium text-white hover:bg-blue-600 disabled:opacity-50"
            >
              {loading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
              {loading ? "Analyzing..." : "Analyze Repository"}
            </button>
            {error && (
              <div className="flex items-center gap-2 rounded-md border border-red-500/40 bg-red-500/10 p-3 text-sm text-red-400">
                <AlertCircle className="h-4 w-4" />
                {error}
              </div>
            )}
          </div>
          <p className="mt-6 text-xs text-muted">Supports public Python repositories. No GitHub login required.</p>
        </main>
      </div>
    );
  }

  if (screen === "analyzing") {
    const stages = ["validating", "cloning", "discovering", "parsing", "building_graph", "calculating_impact", "completed"];
    const currentIndex = stages.indexOf(status?.stage || "queued");
    return (
      <div className="flex min-h-screen flex-col">
        <header className="border-b border-border bg-card">
          <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
            <div className="flex items-center gap-3">
              <GitBranch className="h-5 w-5 text-accent" />
              <h1 className="text-lg font-semibold">CodeGenome</h1>
            </div>
            <span className="text-xs text-muted">Analysis in progress</span>
          </div>
        </header>
        <main className="mx-auto flex w-full max-w-2xl flex-1 flex-col justify-center px-6 py-16">
          <h2 className="mb-2 text-center text-2xl font-semibold">{selectedRepo?.owner}/{selectedRepo?.name}</h2>
          <p className="mb-8 text-center text-muted">{status?.message || "Initializing..."}</p>
          <div className="space-y-3">
            {stages.map((stage, idx) => (
              <div key={stage} className="flex items-center gap-3 text-sm">
                <span className={`h-2 w-2 rounded-full ${idx <= currentIndex ? "bg-accent" : "bg-border"}`} />
                <span className={idx <= currentIndex ? "text-foreground" : "text-muted"}>{stage.replace("_", " ")}</span>
              </div>
            ))}
          </div>
          <div className="mt-8 h-1 w-full overflow-hidden rounded-full bg-border">
            <div className="h-full bg-accent transition-all" style={{ width: `${status?.progress || 0}%` }} />
          </div>
          <p className="mt-2 text-center text-xs text-muted">{status?.progress || 0}%</p>
        </main>
      </div>
    );
  }

  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-border bg-card">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-6 py-4">
          <div className="flex items-center gap-3">
            <GitBranch className="h-5 w-5 text-accent" />
            <h1 className="text-lg font-semibold">CodeGenome</h1>
          </div>
          <span className="text-xs text-muted">{selectedRepo?.owner}/{selectedRepo?.name}</span>
        </div>
      </header>
      <main className="mx-auto w-full max-w-6xl flex-1 px-6 py-8">
        <div className="mb-6 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">{selectedRepo?.owner}/{selectedRepo?.name}</h2>
            <p className="text-xs text-muted">{selectedRepo?.url}</p>
          </div>
          <button
            onClick={() => { setScreen("input"); setSelectedRepo(null); setAnalysis(null); setImpacts([]); setGraph(null); setFunctions([]); setImpactResult(null); setError(null); }}
            className="rounded-md border border-border px-3 py-2 text-xs hover:bg-card"
          >
            Analyze Another Repository
          </button>
        </div>

        <div className="grid grid-cols-1 gap-6 lg:grid-cols-12">
          <div className="lg:col-span-4 space-y-4">
            <div className="rounded-lg border border-border bg-card p-4">
              <h2 className="text-sm font-medium text-muted">Repository Statistics</h2>
              <div className="mt-3 grid grid-cols-2 gap-2 text-xs">
                <div><p className="text-muted">Files</p><p className="font-mono">{functions.length > 0 ? "parsed" : "—"}</p></div>
                <div><p className="text-muted">Functions</p><p className="font-mono">{functions.length}</p></div>
                <div><p className="text-muted">Graph Nodes</p><p className="font-mono">{graph?.nodes.length || 0}</p></div>
                <div><p className="text-muted">Relationships</p><p className="font-mono">{graph?.edges.length || 0}</p></div>
              </div>
            </div>

            <div className="rounded-lg border border-border bg-card p-4">
              <h2 className="text-sm font-medium text-muted">Search Functions</h2>
              <div className="mt-3 flex items-center gap-2">
                <Search className="h-4 w-4 text-muted" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder="calculate_discount"
                  className="h-9 w-full rounded-md border border-border bg-background px-3 text-xs focus:outline-none focus:ring-1 focus:ring-accent"
                />
              </div>
              <div className="mt-2 max-h-60 overflow-y-auto">
                {filteredFunctions.map((f) => (
                  <button
                    key={f.id}
                    onClick={() => setSelectedFunction(f)}
                    className={`w-full rounded-md px-3 py-2 text-left text-xs ${selectedFunction?.id === f.id ? "bg-accent/10 text-accent" : "hover:bg-background"}`}
                  >
                    <p className="font-mono">{f.qualified_name}</p>
                    <p className="text-muted">{f.file_path}:{f.lineno}</p>
                  </button>
                ))}
              </div>
              {selectedFunction && (
                <button
                  onClick={handleAnalyzeImpact}
                  className="mt-3 inline-flex w-full items-center justify-center gap-2 rounded-md bg-accent px-4 py-2 text-xs font-medium text-white hover:bg-blue-600"
                >
                  <Play className="h-3 w-3" />
                  Analyze Impact
                </button>
              )}
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

            {impactResult && (
              <div className="rounded-lg border border-border bg-card p-4">
                <h2 className="text-sm font-medium text-muted">Impact Analysis</h2>
                <div className="mt-3 space-y-2">
                  <div className="flex items-center justify-between">
                    <p className="font-mono text-sm">{impactResult.function}</p>
                    <span className="text-xs text-muted">{impactResult.impact_level}</span>
                  </div>
                  <p className="text-2xl font-semibold">{impactResult.impact_score}<span className="text-sm text-muted">/ 100</span></p>
                  <div className="space-y-1">
                    {impactResult.affected_components.map((comp) => (
                      <div key={comp} className="flex items-center justify-between rounded border border-border bg-background px-3 py-2">
                        <span className="font-mono text-xs">{comp}</span>
                        <span className="text-xs">{impactResult.impact_level || "MEDIUM"}</span>
                      </div>
                    ))}
                  </div>
                  {impactResult.reasons.length > 0 && (
                    <div>
                      <p className="text-xs text-muted">Why:</p>
                      <p className="text-xs">{impactResult.reasons[0]}</p>
                    </div>
                  )}
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
                <h2 className="text-sm font-medium text-muted">Changed Functions</h2>
                {impacts.map((i) => (
                  <p key={i.id} className="mt-2 font-mono text-sm">{i.changed_function}</p>
                ))}
              </div>
            )}
          </div>

          <div className="lg:col-span-8 space-y-4">
            {analysis && (
              <div className="rounded-lg border border-border bg-card p-4">
                <h2 className="text-sm font-medium text-muted">Software Genome</h2>
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