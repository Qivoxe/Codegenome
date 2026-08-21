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
  owner: string;
  url: string;
  status: string;
  created_at: string;
  updated_at: string;
};

export type AnalysisRun = {
  id: string;
  repository_id: string;
  commit_hash: string;
  commit_message: string;
  status: string;
  stage: string;
  progress: number;
  message: string;
  created_at: string;
};

export type AnalysisStatus = {
  analysis_id: string;
  status: string;
  stage: string;
  progress: number;
  message: string;
};

export type FunctionInfo = {
  id: string;
  qualified_name: string;
  file_path: string;
  lineno: number;
  end_lineno: number | null;
  change_type: string;
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

export type ImpactAnalysisRequest = {
  function_id: string;
};

export type ImpactAnalysisResponse = {
  function: string;
  impact_score: number;
  impact_level: string;
  affected_components: string[];
  paths: string[][];
  reasons: string[];
};

export const listRepositories = async () => {
  const response = await api.get<Repository[]>("/repositories");
  return response.data;
};

export const createRepository = async (path: string) => {
  const response = await api.post<Repository>("/repositories", { path });
  return response.data;
};

export const registerGitHubRepo = async (url: string) => {
  const response = await api.post<Repository>("/repositories/github", { url });
  return response.data;
};

export const runAnalysis = async (repositoryId: string) => {
  const response = await api.post<AnalysisRun>("/analyze", { repository_id: repositoryId });
  return response.data;
};

export const getAnalysisStatus = async (analysisId: string) => {
  const response = await api.get<AnalysisStatus>(`/analysis/${analysisId}/status`);
  return response.data;
};

export const getAnalysisFunctions = async (analysisId: string) => {
  const response = await api.get<FunctionInfo[]>(`/analysis/${analysisId}/functions`);
  return response.data;
};

export const getImpactResults = async (analysisId: string) => {
  const response = await api.get<ImpactResult[]>(`/analysis/${analysisId}/impact`);
  return response.data;
};

export const analyzeFunctionImpact = async (analysisId: string, functionId: string) => {
  const response = await api.post<ImpactAnalysisResponse>(`/analysis/${analysisId}/impact`, { function_id: functionId });
  return response.data;
};

export const getGraphData = async (analysisId: string) => {
  const response = await api.get<GraphData>(`/analysis/${analysisId}/graph`);
  return response.data;
};
