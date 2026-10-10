import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { api, type Background, type Health, type ProjectSummary } from './api'
import { play } from './audio'
import { fallbackBackground, TAGLISH_ENABLED } from './options'
import type { BackgroundId, NewVideoDraft, Speaker, Video, VoiceStyle } from './types'
import { isActive, toVideo } from './videos'

/**
 * App-wide state: the video library, engine status, backgrounds, and the "new video" draft.
 * Per-video state (script, style, render) lives in useProject.
 */
interface Store {
  videos: Video[]
  /** False until the first library load finishes (or fails). */
  videosLoaded: boolean
  videosError: string | null
  reloadVideos: () => Promise<void>
  health: Health | null
  /** False until the first engine check has answered (or failed). */
  healthChecked: boolean
  /** Display name from the engine's USER_NAME setting; empty when not set. */
  userName: string
  backgrounds: Background[]
  background: (id: BackgroundId | null | undefined) => {
    name: string
    shortName: string
    from: string
    to: string
    previewUrl?: string
  }
  defaultBackground: BackgroundId
  reloadBackgrounds: () => Promise<Background[]>
  uploadBackground: (file: File) => Promise<Background>
  draft: NewVideoDraft
  updateDraft: (patch: Partial<NewVideoDraft>) => void
  /** Upload the file (or notes) and start writing the script. Resolves with the new video id. */
  startNewVideo: (input?: Partial<NewVideoDraft>) => Promise<string>
  playVoiceSample: (speaker: Speaker, style?: VoiceStyle) => Promise<void>
}

const StoreContext = createContext<Store | null>(null)

const EMPTY_DRAFT: NewVideoDraft = { file: null, notes: '', lengthSec: 60, taglish: TAGLISH_ENABLED }

export function StoreProvider({ children }: { children: ReactNode }) {
  const [projects, setProjects] = useState<ProjectSummary[]>([])
  const [videosLoaded, setVideosLoaded] = useState(false)
  const [videosError, setVideosError] = useState<string | null>(null)
  const [health, setHealth] = useState<Health | null>(null)
  const [healthChecked, setHealthChecked] = useState(false)
  const [backgrounds, setBackgrounds] = useState<Background[]>([])
  const [draft, setDraft] = useState<NewVideoDraft>(EMPTY_DRAFT)
  const draftRef = useRef(draft)
  useEffect(() => {
    draftRef.current = draft
  })

  const reloadVideos = useCallback(async () => {
    try {
      setProjects(await api.listProjects())
      setVideosError(null)
    } catch (err) {
      setVideosError(err instanceof Error ? err.message : String(err))
    } finally {
      setVideosLoaded(true)
    }
  }, [])

  // Library: load now, and keep refreshing while a script or render is in progress.
  const busy = projects.some((p) => p.status === 'generating' || isActive(p.latest_render))
  useEffect(() => {
    reloadVideos()
    const id = setInterval(reloadVideos, busy ? 2500 : 15000)
    return () => clearInterval(id)
  }, [reloadVideos, busy])

  const reloadBackgrounds = useCallback(async () => {
    const next = await api.backgrounds()
    setBackgrounds(next)
    return next
  }, [])

  const uploadBackground = useCallback(async (file: File) => {
    const background = await api.uploadBackground(file)
    await reloadBackgrounds()
    return background
  }, [reloadBackgrounds])

  // Engine status for the sidebar card and greeting; backgrounds once.
  useEffect(() => {
    const load = () =>
      api
        .health()
        .then(setHealth, () => setHealth(null))
        .finally(() => setHealthChecked(true))
    load()
    reloadBackgrounds().catch(() => {})
    const id = setInterval(load, 20000)
    return () => clearInterval(id)
  }, [reloadBackgrounds])

  const defaultBackground = backgrounds[0]?.id ?? 'parkour'

  const background = useCallback<Store['background']>(
    (id) => {
      const bg = backgrounds.find((b) => b.id === id)
      return bg
        ? {
            name: bg.name,
            shortName: bg.short_name,
            from: bg.from,
            to: bg.to,
            previewUrl: bg.preview_url ? api.mediaUrl(bg.preview_url) : undefined,
          }
        : fallbackBackground
    },
    [backgrounds],
  )

  const updateDraft = useCallback<Store['updateDraft']>((patch) => setDraft((d) => ({ ...d, ...patch })), [])

  const startNewVideo = useCallback<Store['startNewVideo']>(
    async (input) => {
      const source = { ...draftRef.current, ...input }
      if (!source.file && !source.notes.trim()) throw new Error('Choose a file or paste some notes first.')
      const project = await api.createProject({
        file: source.file,
        notes: source.file ? undefined : source.notes,
        lengthSec: source.lengthSec,
        taglish: source.taglish,
      })
      await api.generateScript(project.id)
      setDraft(EMPTY_DRAFT)
      reloadVideos()
      return project.id
    },
    [reloadVideos],
  )

  const playVoiceSample = useCallback<Store['playVoiceSample']>(
    (speaker, style = 'quick') => play(`sample:${speaker}`, api.sampleUrl(speaker, style)),
    [],
  )

  const value = useMemo<Store>(
    () => ({
      videos: projects.map((p) => toVideo(p, defaultBackground)),
      videosLoaded,
      videosError,
      reloadVideos,
      health,
      healthChecked,
      userName: health?.user_name ?? '',
      backgrounds,
      background,
      defaultBackground,
      reloadBackgrounds,
      uploadBackground,
      draft,
      updateDraft,
      startNewVideo,
      playVoiceSample,
    }),
    [
      projects,
      videosLoaded,
      videosError,
      reloadVideos,
      health,
      healthChecked,
      backgrounds,
      background,
      defaultBackground,
      reloadBackgrounds,
      uploadBackground,
      draft,
      updateDraft,
      startNewVideo,
      playVoiceSample,
    ],
  )

  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>
}

export function useStore(): Store {
  const store = useContext(StoreContext)
  if (!store) throw new Error('useStore must be used inside <StoreProvider>')
  return store
}
