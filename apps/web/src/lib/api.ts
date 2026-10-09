/**
 * Client for the local engine (FastAPI, server/). Everything is same-origin under /api:
 * in production the server serves this app, in `npm run dev` Vite proxies /api to it.
 */
import type { CaptionStyle, VideoLength } from './types'

export type ProjectStatus = 'ready' | 'generating' | 'scripted' | 'failed'
export type ScriptStep = 'ideas' | 'jokes' | 'check'
export type RenderStatus = 'queued' | 'running' | 'done' | 'failed' | 'canceled'
export type RenderStep = 'voices' | 'captions' | 'mixing' | 'rendering' | 'done'

export interface ApiLine {
  id: string
  position: number
  character_id: string
  text: string
  seconds: number
  voiced: boolean
}

export interface Render {
  id: string
  project_id: string
  status: RenderStatus
  step: RenderStep | null
  progress: number
  background_id: string | null
  caption_style: CaptionStyle | null
  duration_s: number | null
  error: string | null
  video_url: string | null
  created_at: string
}

export interface ProjectSummary {
  id: string
  title: string
  subject: string | null
  status: ProjectStatus
  script_step: ScriptStep | null
  page_count: number
  line_count: number
  length_s: VideoLength
  background_id: string | null
  created_at: string
  latest_render: Render | null
  video: Render | null
}

export interface Project {
  id: string
  title: string
  subject: string | null
  status: ProjectStatus
  error: string | null
  source_kind: 'pdf' | 'text' | 'notes'
  source_name: string | null
  page_count: number
  pages: string | null
  text_preview: string
  text_chars: number
  length_s: VideoLength
  taglish: boolean
  script_step: ScriptStep | null
  script_started_at: string | null
  key_ideas: string[]
  background_id: string | null
  caption_style: CaptionStyle
  lines: ApiLine[]
  renders: Render[]
  video: Render | null
  created_at: string
}

export interface Background {
  id: string
  name: string
  short_name: string
  from: string
  to: string
  has_clip: boolean
}

export interface Character {
  id: string
  name: string
  role: 'asker' | 'explainer'
  vibe: string
  color: string
  has_image: boolean
}

export interface EngineStatus {
  ok: boolean
  detail: string
}

export interface Health {
  ok: boolean
  user_name: string
  auth_required: boolean
  auth_ok: boolean
  ready: boolean
  engines: Record<'llm' | 'tts' | 'alignment' | 'ffmpeg', EngineStatus>
}

export interface LineDraft {
  id?: string
  character_id: string
  text: string
}

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
  ) {
    super(message)
  }
}

const BASE = '/api'
const TOKEN_KEY = 'brainrot.pairing-token'

/**
 * Pairing token (only when the server sets API_PAIRING_TOKEN). Open the app once as
 * http://<laptop>:8000/?token=<token> and it is remembered on that device.
 */
function token(): string {
  try {
    const fromUrl = new URLSearchParams(window.location.search).get('token')
    if (fromUrl) localStorage.setItem(TOKEN_KEY, fromUrl)
    return fromUrl ?? localStorage.getItem(TOKEN_KEY) ?? ''
  } catch {
    return ''
  }
}

function withToken(url: string): string {
  const t = token()
  return t ? `${url}${url.includes('?') ? '&' : '?'}token=${encodeURIComponent(t)}` : url
}

async function errorMessage(response: Response): Promise<string> {
  try {
    const body = await response.json()
    if (typeof body.detail === 'string') return body.detail
    if (Array.isArray(body.detail) && body.detail[0]?.msg) return body.detail[0].msg
  } catch {
    // not JSON
  }
  if (response.status === 401) return 'This device needs the pairing token. Open the app with ?token=…'
  return `The engine returned an error (${response.status})`
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers)
  const t = token()
  if (t) headers.set('X-Pairing-Token', t)
  let response: Response
  try {
    response = await fetch(`${BASE}${path}`, { ...init, headers })
  } catch {
    throw new ApiError("Can't reach the engine on your laptop. Is it running?", 0)
  }
  if (!response.ok) throw new ApiError(await errorMessage(response), response.status)
  if (response.status === 204) return undefined as T
  return (await response.json()) as T
}

const json = (method: string, body: unknown): RequestInit => ({
  method,
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})

export const api = {
  health: () => request<Health>('/health'),
  characters: () => request<Character[]>('/assets/characters'),
  backgrounds: () => request<Background[]>('/assets/backgrounds'),

  listProjects: () => request<ProjectSummary[]>('/projects'),
  getProject: (id: string) => request<Project>(`/projects/${id}`),
  createProject(input: { file?: File | null; notes?: string; lengthSec: VideoLength; taglish: boolean }) {
    const form = new FormData()
    if (input.file) form.append('file', input.file, input.file.name)
    else if (input.notes) form.append('notes', input.notes)
    form.append('length_s', String(input.lengthSec))
    form.append('taglish', String(input.taglish))
    return request<Project>('/projects', { method: 'POST', body: form })
  },
  updateProject: (
    id: string,
    patch: Partial<{ title: string; background_id: string; caption_style: CaptionStyle; taglish: boolean; length_s: VideoLength }>,
  ) => request<Project>(`/projects/${id}`, json('PATCH', patch)),
  deleteProject: (id: string) => request<void>(`/projects/${id}`, { method: 'DELETE' }),

  generateScript: (id: string) => request<Project>(`/projects/${id}/script`, { method: 'POST' }),
  saveScript: (id: string, lines: LineDraft[]) => request<Project>(`/projects/${id}/script`, json('PUT', { lines })),
  previewLine: (lineId: string) =>
    request<{ audio_url: string; duration_s: number }>(`/lines/${lineId}/preview`, { method: 'POST' }),

  startRender: (projectId: string, style: { background_id?: string; caption_style?: CaptionStyle } = {}) =>
    request<Render>(`/projects/${projectId}/renders`, json('POST', style)),
  getRender: (id: string) => request<Render>(`/renders/${id}`),
  cancelRender: (id: string) => request<Render>(`/renders/${id}`, { method: 'DELETE' }),
  revealRender: (id: string) => request<void>(`/renders/${id}/reveal`, { method: 'POST' }),

  /** URLs for <audio>/<video>/<a>, which can't send headers: the token goes in the query. */
  mediaUrl: (path: string) => withToken(path),
  videoUrl: (render: Render, download = false) =>
    withToken(`${render.video_url ?? `${BASE}/renders/${render.id}/video`}${download ? '?download=1' : ''}`),
  sampleUrl: (characterId: string) => withToken(`${BASE}/assets/characters/${characterId}/sample`),
}
