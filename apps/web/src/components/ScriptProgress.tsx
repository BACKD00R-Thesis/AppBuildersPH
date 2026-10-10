import { useEffect, useState } from 'react'
import type { Project } from '../lib/api'
import { keyIdeasForLength, scriptSecondsForLength } from '../lib/options'
import { speakerOf } from '../lib/speakers'
import { scriptSteps } from '../lib/videos'
import { Steps } from './Steps'

/** Ticks every second while `active`, for countdowns. */
function useNow(active: boolean): number {
  const [now, setNow] = useState(() => Date.now())
  useEffect(() => {
    if (!active) return
    const id = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(id)
  }, [active])
  return now
}

/** "About 40 seconds left", from when the script job started and a typical duration for the length. */
export function useSecondsLeft(project: Project | null): string {
  const generating = project?.status === 'generating'
  const now = useNow(generating)
  if (!project || !generating) return ''
  const started = project.script_started_at ? new Date(project.script_started_at).getTime() : now
  const left = Math.round(scriptSecondsForLength[project.length_s] - (now - started) / 1000)
  return left > 5 ? `About ${left} seconds left` : 'Almost done'
}

export function scriptHeadline(project: Project): string {
  const reader = speakerOf('tito-boy').name
  return project.source_kind === 'pdf' ? `${reader} is reading your PDF` : `${reader} is reading your notes`
}

/** Figma: Steps, for the script job (read, key ideas, jokes, check). */
export function ScriptSteps({ project, density }: { project: Project; density: 'desktop' | 'mobile' }) {
  const ideas = keyIdeasForLength[project.length_s]
  const steps = scriptSteps(project)
  const ideasDone = steps.find((s) => s.id === 'ideas')?.status === 'done'
  const labels: Record<string, string> = {
    read: project.page_count > 0 ? `Read ${project.page_count} pages` : 'Read your notes',
    ideas: ideasDone ? 'Found the key ideas' : `Finding about ${ideas} key ideas`,
    jokes: 'Writing the jokes',
    check: project.source_kind === 'pdf' ? 'Checking lines against your PDF' : 'Checking the lines',
  }
  return <Steps density={density} items={steps.map((step) => ({ ...step, label: labels[step.id] ?? step.id }))} />
}
