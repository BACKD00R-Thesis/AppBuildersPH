import { useCallback, useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'
import { play, stop, usePlaying } from '../lib/audio'
import type { ScriptLine } from '../lib/types'
import type { ProjectHandle } from '../lib/useProject'
import { toScriptLines } from '../lib/videos'
import { ScriptLineCard } from './ScriptLineCard'

let newLineCount = 0

const same = (a: ScriptLine[], b: ScriptLine[]) =>
  a.length === b.length && a.every((l, i) => l.id === b[i].id && l.text.trim() === b[i].text && l.speaker === b[i].speaker)

/**
 * The script being edited, which line is playing, and which is being edited.
 * Edits are saved to the engine when a line is done ("Done" / Enter), before a changed line is
 * previewed, and before leaving the script (`save`). Lines left empty are dropped on save.
 */
export function useScriptEditing(handle: ProjectHandle) {
  const { project, setProject, setError } = handle
  const [lines, setLines] = useState<ScriptLine[]>([])
  const [editingId, setEditingId] = useState<string | null>(null)
  const [loadingId, setLoadingId] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)
  const playing = usePlaying()
  const saved = useRef<ScriptLine[]>([])
  const pending = useRef<Promise<boolean>>(Promise.resolve(true))
  const linesRef = useRef(lines)
  useEffect(() => {
    linesRef.current = lines
  })

  // Take the engine's script whenever it changes (first load, a rewrite finished, a save returned).
  // Keyed on a string so polling with an unchanged script doesn't reset the editor.
  const serverVersion = project ? project.lines.map((l) => `${l.id}:${l.character_id}:${l.text}:${l.seconds}`).join('|') : null
  useEffect(() => {
    if (!project) return
    const serverLines = toScriptLines(project)
    saved.current = serverLines
    setLines(serverLines)
    // `project` is deliberately not a dependency: only a change in its lines should reset the editor.
  }, [serverVersion])

  const dirty = !same(lines, saved.current)

  const save = useCallback((): Promise<boolean> => {
    if (!project) return Promise.resolve(false)
    // Saves run one after another so a slow save can't overwrite a newer one.
    pending.current = pending.current.then(async () => {
      const toSave = linesRef.current.filter((l) => l.text.trim())
      if (same(toSave, saved.current)) return true
      if (toSave.length === 0) {
        setError('Write at least one line.')
        return false
      }
      setSaving(true)
      try {
        const next = await api.saveScript(
          project.id,
          toSave.map((l) => ({ id: l.id.startsWith('new-') ? undefined : l.id, character_id: l.speaker, text: l.text.trim() })),
        )
        setProject(next)
        return true
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err))
        return false
      } finally {
        setSaving(false)
      }
    })
    return pending.current
  }, [project, setProject, setError])

  const updateLine = useCallback((id: string, text: string) => {
    setLines((list) => list.map((l) => (l.id === id ? { ...l, text } : l)))
  }, [])

  const addAndEdit = useCallback(() => {
    const id = `new-${++newLineCount}`
    setLines((list) => {
      const last = list[list.length - 1]
      const speaker = last?.speaker === 'tito-boy' ? 'bunso' : 'tito-boy'
      return [...list, { id, speaker, text: '', seconds: 0 }]
    })
    setEditingId(id)
  }, [])

  const done = useCallback(() => {
    setEditingId(null)
    save()
  }, [save])

  const playLine = useCallback(
    async (line: ScriptLine) => {
      if (playing === line.id) {
        stop()
        return
      }
      if (!line.text.trim()) return
      setLoadingId(line.id)
      try {
        let lineId = line.id
        if (lineId.startsWith('new-') || dirty) {
          setEditingId(null)
          const index = linesRef.current.filter((l) => l.text.trim()).findIndex((l) => l.id === line.id)
          if (!(await save())) return
          lineId = saved.current[index]?.id ?? lineId
        }
        const { audio_url } = await api.previewLine(lineId)
        await play(lineId, api.mediaUrl(audio_url))
        handle.reload() // the line now has its real length
      } catch (err) {
        setError(err instanceof Error ? err.message : String(err))
      } finally {
        setLoadingId(null)
      }
    },
    [playing, dirty, save, handle, setError],
  )

  return { lines, editingId, setEditingId, playingId: playing, loadingId, dirty, saving, save, updateLine, addAndEdit, done, playLine }
}

interface Props {
  editing: ReturnType<typeof useScriptEditing>
  density: 'desktop' | 'mobile'
  editHint: string
}

export function ScriptList({ editing, density, editHint }: Props) {
  const { lines, editingId, playingId, loadingId, setEditingId, updateLine, done, playLine } = editing

  return (
    <>
      {lines.map((line) => (
        <ScriptLineCard
          key={line.id}
          line={line}
          density={density}
          editHint={editHint}
          state={editingId === line.id ? 'editing' : playingId === line.id ? 'playing' : 'idle'}
          loading={loadingId === line.id}
          onPlay={() => playLine(line)}
          onEdit={() => setEditingId(line.id)}
          onChange={(text) => updateLine(line.id, text)}
          onDone={done}
        />
      ))}
    </>
  )
}
