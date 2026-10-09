/** Typed client for the local FastAPI backend (see docs/architecture.md). */

export type ProjectStatus = 'ready' | 'generating' | 'scripted' | 'failed';
export type RenderStatus = 'queued' | 'running' | 'done' | 'failed' | 'canceled';

export interface Line {
  id: string;
  position: number;
  character_id: string;
  text: string;
}

export interface Render {
  id: string;
  project_id: string;
  status: RenderStatus;
  step: string | null;
  progress: number;
  background_id: string | null;
  duration_s: number | null;
  error: string | null;
  video_url: string | null;
  created_at: string;
}

export interface Project {
  id: string;
  title: string;
  status: ProjectStatus;
  error: string | null;
  page_count: number;
  pages: string | null;
  text_preview: string;
  text_chars: number;
  lines: Line[];
  renders: Render[];
  created_at: string;
}

export interface ProjectSummary {
  id: string;
  title: string;
  status: ProjectStatus;
  page_count: number;
  created_at: string;
  latest_render: Render | null;
}

export interface Character {
  id: string;
  name: string;
  role: 'asker' | 'explainer';
  persona: string;
  color: string;
  has_image: boolean;
}

export interface Background {
  id: string;
  name: string;
  builtin: boolean;
}

export interface EngineStatus {
  ok: boolean;
  detail: string;
}

export interface Health {
  ok: boolean;
  auth_required: boolean;
  auth_ok: boolean;
  ready: boolean;
  engines: Record<'llm' | 'tts' | 'alignment' | 'ffmpeg', EngineStatus>;
}

/** A line as sent to PUT /projects/{id}/script. New lines have no id. */
export interface LineDraft {
  id?: string;
  character_id: string;
  text: string;
}

export interface PickedFile {
  uri: string;
  name: string;
  mimeType?: string;
  /** Web only: the browser File object. */
  file?: Blob;
}

export interface ServerConfig {
  apiUrl: string;
  token: string;
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message);
  }
}

const DEFAULT_TIMEOUT_MS = 15_000;
const UPLOAD_TIMEOUT_MS = 120_000;

export function normalizeUrl(url: string): string {
  let value = url.trim().replace(/\/+$/, '');
  if (value && !/^https?:\/\//i.test(value)) value = `http://${value}`;
  return value;
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json();
    if (typeof body.detail === 'string') return body.detail;
    if (Array.isArray(body.detail) && body.detail[0]?.msg) return body.detail[0].msg;
  } catch {
    // not JSON
  }
  return `Server error ${response.status}`;
}

export function createApi(config: ServerConfig) {
  const base = normalizeUrl(config.apiUrl);
  const headers: Record<string, string> = config.token ? { 'X-Pairing-Token': config.token } : {};

  async function request<T>(
    path: string,
    init: RequestInit & { timeoutMs?: number } = {},
  ): Promise<T> {
    if (!base) throw new ApiError('Set the server address in Settings first.', 0);
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), init.timeoutMs ?? DEFAULT_TIMEOUT_MS);
    let response: Response;
    try {
      response = await fetch(`${base}${path}`, {
        ...init,
        headers: { ...headers, ...(init.headers as Record<string, string>) },
        signal: controller.signal,
      });
    } catch {
      throw new ApiError(
        `Can't reach the server at ${base}. Check that it's running and on the same Wi-Fi.`,
        0,
      );
    } finally {
      clearTimeout(timer);
    }
    if (!response.ok) throw new ApiError(await errorMessage(response), response.status);
    if (response.status === 204) return undefined as T;
    return (await response.json()) as T;
  }

  const json = (method: string, body: unknown): RequestInit => ({
    method,
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  return {
    baseUrl: base,
    headers,

    /** Absolute URL for media served by the API (audio previews, videos). */
    mediaUrl(path: string): string {
      return `${base}${path}`;
    },

    health: () => request<Health>('/health', { timeoutMs: 5_000 }),
    characters: () => request<Character[]>('/assets/characters'),
    backgrounds: () => request<Background[]>('/assets/backgrounds'),
    characterImageUrl: (id: string) => `${base}/assets/characters/${id}/image`,

    listProjects: () => request<ProjectSummary[]>('/projects'),
    getProject: (id: string) => request<Project>(`/projects/${id}`),
    renameProject: (id: string, title: string) =>
      request<Project>(`/projects/${id}`, json('PATCH', { title })),
    deleteProject: (id: string) => request<void>(`/projects/${id}`, { method: 'DELETE' }),

    uploadProject(file: PickedFile, options: { title?: string; pages?: string }) {
      const form = new FormData();
      if (file.file) {
        form.append('file', file.file, file.name);
      } else {
        // React Native's FormData accepts { uri, name, type } for local files.
        form.append('file', {
          uri: file.uri,
          name: file.name,
          type: file.mimeType ?? 'application/pdf',
        } as unknown as Blob);
      }
      if (options.title) form.append('title', options.title);
      if (options.pages) form.append('pages', options.pages);
      return request<Project>('/projects', {
        method: 'POST',
        body: form,
        timeoutMs: UPLOAD_TIMEOUT_MS,
      });
    },

    generateScript: (id: string) =>
      request<Project>(`/projects/${id}/script`, { method: 'POST' }),
    saveScript: (id: string, lines: LineDraft[]) =>
      request<Project>(`/projects/${id}/script`, json('PUT', { lines })),
    previewLine: (lineId: string) =>
      request<{ audio_url: string; duration_s: number }>(`/lines/${lineId}/preview`, {
        method: 'POST',
        timeoutMs: 60_000,
      }),

    startRender: (projectId: string, backgroundId: string | null) =>
      request<Render>(
        `/projects/${projectId}/renders`,
        json('POST', { background_id: backgroundId }),
      ),
    getRender: (id: string) => request<Render>(`/renders/${id}`),
    cancelRender: (id: string) => request<Render>(`/renders/${id}`, { method: 'DELETE' }),
  };
}

export type Api = ReturnType<typeof createApi>;
