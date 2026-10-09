/** Turns the engine's projects into the UI's video cards, and decides which screen a video opens on. */
import type { Project, ProjectSummary, Render } from './api'
import { captionFromText } from './format'
import type { ScriptLine, Step, StepStatus, Video } from './types'

const DAY_MS = 24 * 60 * 60 * 1000

export const isActive = (render: Render | null | undefined) =>
  !!render && (render.status === 'queued' || render.status === 'running')

type Routable = Pick<ProjectSummary, 'id' | 'status' | 'latest_render' | 'video'> & { line_count?: number }

/** The screen for the step a video is at. */
export function videoHref(project: Routable): string {
  const base = `/videos/${project.id}`
  if (project.status === 'generating' || project.status === 'ready') return `${base}/writing`
  if (project.status === 'failed' && !project.line_count) return `${base}/writing`
  if (isActive(project.latest_render)) return `${base}/rendering`
  if (project.video) return base
  return `${base}/script`
}

function progressLabel(p: ProjectSummary): string | null {
  if (p.status === 'generating') return 'Writing the script'
  if (p.status === 'ready') return 'Not started'
  if (p.status === 'failed' && !p.line_count) return 'Couldn’t write the script'
  if (isActive(p.latest_render)) return `Rendering, ${Math.round((p.latest_render?.progress ?? 0) * 100)}%`
  if (p.video) return null
  if (p.latest_render?.status === 'failed') return 'Render failed'
  return 'Script ready'
}

export function toVideo(p: ProjectSummary, fallbackBackground: string): Video {
  return {
    id: p.id,
    title: p.title,
    subject: p.subject ?? 'Study notes',
    durationSec: Math.round(p.video?.duration_s ?? p.length_s),
    caption: captionFromText(p.title),
    lineCount: p.line_count,
    background: p.video?.background_id ?? p.background_id ?? fallbackBackground,
    isNew: !!p.video && Date.now() - new Date(p.video.created_at).getTime() < DAY_MS,
    href: videoHref(p),
    progressLabel: progressLabel(p),
    hasVideo: !!p.video,
    madeAt: p.video?.created_at ?? null,
  }
}

const asSummary = (p: Project): ProjectSummary => ({ ...p, line_count: p.lines.length, latest_render: p.renders[0] ?? null })

/** Same as toVideo, from a full project (detail screens). */
export function projectVideo(p: Project, fallbackBackground: string): Video {
  return toVideo(asSummary(p), fallbackBackground)
}

/** Same as videoHref, from a full project. */
export function projectHref(p: Project): string {
  return videoHref(asSummary(p))
}

export function toScriptLines(project: Project): ScriptLine[] {
  return project.lines.map((l) => ({ id: l.id, speaker: l.character_id, text: l.text, seconds: l.seconds }))
}

/** Total spoken length of a script, in seconds (for "about 58s"). */
export function scriptSeconds(lines: ScriptLine[]): number {
  return Math.round(lines.reduce((sum, l) => sum + l.seconds, 0) + Math.max(lines.length - 1, 0) * 0.25)
}

function stepsFrom(order: string[], current: string | null, done: boolean): Step[] {
  const index = done ? order.length : Math.max(order.indexOf(current ?? ''), 0)
  return order.map((id, i) => ({ id, status: (i < index ? 'done' : i === index ? 'current' : 'pending') as StepStatus }))
}

/** "Writing script" steps: read (done once writing starts), ideas, jokes, check. */
export function scriptSteps(project: Project): Step[] {
  const steps = stepsFrom(['read', 'ideas', 'jokes', 'check'], project.script_step ?? 'ideas', false)
  return project.status === 'generating' ? steps : steps.map((s) => ({ ...s, status: 'pending' }))
}

/** Render steps, mapped from the engine's step names to the design's. */
export function renderSteps(render: Render | null | undefined): Step[] {
  const engine = ['voices', 'captions', 'mixing', 'rendering']
  const steps = stepsFrom(engine, render?.step ?? 'voices', render?.status === 'done')
  const ids: Record<string, string> = { voices: 'voice', captions: 'captions', mixing: 'mix', rendering: 'export' }
  return steps.map((s) => ({ ...s, id: ids[s.id] }))
}
