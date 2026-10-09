import { useEffect } from 'react'
import { Navigate, useNavigate, useParams } from 'react-router-dom'
import { Button } from '../../components/Button'
import { Notice, NoticeAction } from '../../components/Notice'
import { ScriptList, useScriptEditing } from '../../components/ScriptList'
import { MobileBottomBar, MobileShell, MobileTitleRow } from '../../layouts/MobileShell'
import { useProject } from '../../lib/useProject'
import { scriptSeconds } from '../../lib/videos'

/** Figma: Mobile v2 / Script editor (14:200) */
export function ScriptEditor() {
  const { id } = useParams()
  const navigate = useNavigate()
  const handle = useProject(id)
  const { project, video, error, setError, notFound } = handle
  const editing = useScriptEditing(handle)

  // While the script is being (re)written, the writing screen shows progress.
  const writing = project?.status === 'generating' || project?.status === 'ready'
  useEffect(() => {
    if (writing) navigate(`/videos/${id}/writing`, { replace: true })
  }, [writing, id, navigate])

  if (notFound) return <Navigate to="/" replace />
  if (!project || !video) return null

  const toStyle = async () => {
    if (await editing.save()) navigate(`/videos/${project.id}/style`)
  }

  return (
    <MobileShell
      headerClassName="gap-[10px] pb-[22px]"
      bodyClassName="gap-3"
      header={
        <>
          <MobileTitleRow backTo={video.hasVideo ? `/videos/${project.id}` : '/'} title="Script" />
          <div className="flex w-full flex-col gap-1 whitespace-nowrap">
            <p className="eyebrow text-on-green">{video.subject}</p>
            <p className="text-page truncate font-serif text-[26px] font-bold">{video.title}</p>
            <p className="text-on-green text-[13px]">
              {editing.lines.length} lines, about {scriptSeconds(editing.lines)}s
            </p>
          </div>
        </>
      }
      footer={
        <MobileBottomBar>
          <div className="flex w-full gap-[10px]">
            <Button variant="secondary" className="min-w-0 flex-1" onClick={editing.addAndEdit}>
              Add line
            </Button>
            <Button className="min-w-0 flex-1" onClick={toStyle} disabled={editing.saving}>
              Pick a style
            </Button>
          </div>
        </MobileBottomBar>
      }
    >
      {error && (
        <Notice action={<NoticeAction onClick={() => setError(null)}>OK</NoticeAction>}>{error}</Notice>
      )}
      {project.error && <Notice>Couldn’t write a new script: {project.error}</Notice>}
      <ScriptList editing={editing} density="mobile" editHint="Tap play to hear it" />
    </MobileShell>
  )
}
