import { useCallback, useEffect, useMemo, useState } from 'react'
import { api, type Project } from './api'
import { useStore } from './store'
import type { CaptionStyle, Video } from './types'
import { isActive, projectVideo } from './videos'

const POLL_MS = 1200

function message(err: unknown): string {
  return err instanceof Error ? err.message : String(err)
}

/**
 * One video from the engine. Polls while its script is being written or a render is running,
 * and holds the style actions (background, captions, Taglish) and render/regenerate.
 */
export function useProject(id: string | undefined) {
  const { defaultBackground, reloadVideos } = useStore()
  const [project, setProject] = useState<Project | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [notFound, setNotFound] = useState(false)

  const reload = useCallback(async () => {
    if (!id) return
    try {
      const next = await api.getProject(id)
      setProject(next)
      setError(null)
    } catch (err) {
      if (err && typeof err === 'object' && 'status' in err && err.status === 404) setNotFound(true)
      setError(message(err))
    }
  }, [id])

  useEffect(() => {
    setProject(null)
    setNotFound(false)
    reload()
  }, [reload])

  const latestRender = project?.renders[0] ?? null
  const busy = project?.status === 'generating' || isActive(latestRender)
  useEffect(() => {
    if (!busy) return
    const timer = setInterval(reload, POLL_MS)
    return () => clearInterval(timer)
  }, [busy, reload])

  const video: Video | null = useMemo(
    () => (project ? projectVideo(project, defaultBackground) : null),
    [project, defaultBackground],
  )

  const updateStyle = useCallback(
    async (patch: Partial<{ background_id: string; caption_style: CaptionStyle; taglish: boolean }>) => {
      if (!id) return
      setProject((p) => (p ? { ...p, ...patch } : p)) // instant feedback; the server copy follows
      try {
        setProject(await api.updateProject(id, patch))
      } catch (err) {
        setError(message(err))
        reload()
      }
    },
    [id, reload],
  )

  const regenerate = useCallback(async () => {
    if (!id) return
    setError(null)
    try {
      setProject(await api.generateScript(id))
      reloadVideos()
    } catch (err) {
      setError(message(err))
    }
  }, [id, reloadVideos])

  /** Starts a render with the saved style. Resolves true when it started. */
  const startRender = useCallback(async () => {
    if (!project) return false
    setError(null)
    try {
      await api.startRender(project.id, {
        background_id: project.background_id ?? defaultBackground,
        caption_style: project.caption_style,
      })
      await reload()
      reloadVideos()
      return true
    } catch (err) {
      setError(message(err))
      return false
    }
  }, [project, defaultBackground, reload, reloadVideos])

  return {
    project,
    setProject,
    video,
    latestRender,
    error,
    setError,
    notFound,
    reload,
    updateStyle,
    regenerate,
    startRender,
  }
}

export type ProjectHandle = ReturnType<typeof useProject>
