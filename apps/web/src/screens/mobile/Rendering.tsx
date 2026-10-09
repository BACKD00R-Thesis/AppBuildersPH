import { useEffect } from 'react'
import { Navigate, useNavigate, useParams } from 'react-router-dom'
import { Button } from '../../components/Button'
import { Notice } from '../../components/Notice'
import { ProgressBar } from '../../components/ProgressBar'
import { Steps } from '../../components/Steps'
import { MobileBottomBar, MobileShell, MobileTitleRow } from '../../layouts/MobileShell'
import { useStore } from '../../lib/store'
import { useProject } from '../../lib/useProject'
import { isActive, renderSteps } from '../../lib/videos'

/** Figma: Mobile v2 / Rendering (14:347). Opens the player when the render finishes. */
export function Rendering() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { background: backgroundOf, defaultBackground } = useStore()
  const { project, video, latestRender: render, notFound, startRender, error } = useProject(id)

  const done = render?.status === 'done'
  useEffect(() => {
    if (done) navigate(`/videos/${id}`, { replace: true })
  }, [done, id, navigate])

  if (notFound) return <Navigate to="/" replace />
  if (!project || !video) return null
  if (!render) return <Navigate to={`/videos/${project.id}/script`} replace />

  const labels: Record<string, string> = {
    voice: `Voiced ${project.lines.length} lines`,
    captions: 'Synced captions',
    mix: `Mixing in ${backgroundOf(render.background_id ?? project.background_id ?? defaultBackground).name}`,
    export: 'Exporting MP4',
  }
  const stopped = !isActive(render) && !done

  return (
    <MobileShell
      headerClassName="gap-[14px] pb-5"
      bodyClassName="gap-[14px]"
      header={<MobileTitleRow backTo={`/videos/${project.id}/style`} title="Rendering" />}
      footer={
        <MobileBottomBar className="gap-[10px]">
          {stopped && (
            <Button className="w-full" onClick={startRender}>
              Try again
            </Button>
          )}
          <Button variant="ghost" to={`/videos/${project.id}/script`} className="w-full">
            Back to script
          </Button>
        </MobileBottomBar>
      }
    >
      <p className="eyebrow text-green-2 shrink-0">{video.title}</p>
      <p className="text-green shrink-0 font-serif text-[88px] leading-[92px] font-bold whitespace-nowrap">
        {Math.round(render.progress * 100)}%
      </p>
      <h2 className="text-ink w-full shrink-0 font-serif text-[24px] leading-[30px] font-semibold">
        {stopped ? (render.status === 'canceled' ? 'Render canceled' : 'The render stopped') : 'Putting your video together'}
      </h2>
      <ProgressBar value={render.progress} label="Render progress" className="w-full shrink-0" />
      {stopped ? (
        <Notice>{render.error ?? 'The render was canceled.'}</Notice>
      ) : (
        <p className="text-muted w-full shrink-0 text-[14px] leading-[21px]">
          You can leave this page. We’ll let you know when it’s ready.
        </p>
      )}
      {error && <Notice>{error}</Notice>}
      <div className="w-full shrink-0">
        <Steps
          density="mobile"
          items={renderSteps(render).map((step) => ({ ...step, label: labels[step.id] ?? step.id }))}
        />
      </div>
    </MobileShell>
  )
}
