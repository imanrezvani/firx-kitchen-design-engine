// Client + response types for the deterministic AI pipeline
// (POST /api/v1/ai/pipeline → spec + prompt + DesignSpecification).

import { apiGet, apiPost } from "@/lib/api";
import type { KitchenSpecification } from "@/lib/ai-spec";

export interface DesignElement {
  id: string;
  type: string;
  name: string;
  wall?: string | null;
  offset: number;
  x: number;
  y: number;
  z: number;
  rotation: number;
  width_mm: number;
  height_mm: number;
  depth_mm: number;
}

export interface MaterialRef {
  code: string;
  name: string;
  category: string;
}

export interface RenderInstruction {
  view: string;
  name: string;
  instruction: string;
}

export interface PromptSection {
  title: string;
  body: string;
}

export interface PromptDocument {
  spec_version: string;
  layout: string;
  camera_views: string[];
  sections: PromptSection[];
}

export interface DesignSpecification {
  version: string;
  source_spec_version: string;
  layout: string;
  style: string;
  room: Record<string, unknown>;
  cabinets: DesignElement[];
  appliances: DesignElement[];
  countertops: DesignElement[];
  object_positions: Record<string, unknown>[];
  materials: MaterialRef[];
  colors: Record<string, unknown>;
  render_instructions: RenderInstruction[];
  rationale: string;
  warnings: string[];
  score: number;
}

export interface PipelineResult {
  spec: KitchenSpecification;
  prompt: PromptDocument;
  design: DesignSpecification;
}

export type ProviderName = "gpt" | "gemini" | "mock";

export function runPipeline(
  spec: KitchenSpecification,
  provider: ProviderName = "mock",
  cameraViews?: string[],
): Promise<PipelineResult> {
  const q = new URLSearchParams({ provider_name: provider });
  cameraViews?.forEach((v) => q.append("camera_views", v));
  return apiPost<PipelineResult>(
    `/api/v1/ai/pipeline?${q.toString()}`,
    spec,
  );
}

export function validateSpec(spec: KitchenSpecification): Promise<{ valid: boolean; spec: KitchenSpecification }> {
  return apiPost("/api/v1/ai/spec", spec);
}

export function listProviders(): Promise<{ providers: string[]; default: string }> {
  return apiGet("/api/v1/ai/providers");
}
