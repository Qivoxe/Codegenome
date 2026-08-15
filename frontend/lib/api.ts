import axios from "axios";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE || "http://localhost:8000";

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    "Content-Type": "application/json",
  },
});

export type Repository = {
  id: string;
  path: string;
  name: string;
  created_at: string;
  updated_at: string;
};

export type AnalysisRun = {
  id: string;
  repository_id: string;
  commit_hash: string;
  commit_message: string;
  created_at: string;
};

export type ImpactResult = {
  id: string;
  analysis_id: string;
  changed_function: string;
  file_path: string;
  direct_impact: string[];
  transitive_impact: string[];
  impact_score: number;
  impact_level: string;
  explanation: string;
  affected_components: string[];
  impact_paths: string[][];
  nodes: Record<string, unknown>[];
  edges: Record<string, unknown>[];
};

export type GraphData = {
  analysis_id: string;
  nodes: Record<string, unknown>[];
  edges: Record<string, unknown>[];
};

export const listRepositories = async () => {
  const response = await api.get<Repository[]>("/repositories");
  return response.data;
};

export const createRepository = async (path: string) => {
  const response = await api.post<Repository>("/repositories", { path });
  return response.data;
};

export const runAnalysis = async (repositoryId: string) => {
  const response = await api.post<AnalysisRun>("/analyze", { repository_id: repositoryId });
  return response.data;
};

export const getAnalysis = async (analysisId: string) => {
  const response = await api.get<AnalysisRun>(`/analysis/${analysisId}`);
  return response.data;
};

export const getImpactResults = async (analysisId: string) => {
  const response = await api.get<ImpactResult[]>(`/analysis/${analysisId}/impact`);
  return response.data;
};

export const getGraphData = async (analysisId: string) => {
  const response = await api.get<GraphData>(`/analysis/${analysisId}/graph`);
  return response.data;
};
