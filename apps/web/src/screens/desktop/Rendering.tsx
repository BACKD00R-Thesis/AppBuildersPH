import { useEffect } from 'react'
import { Navigate, useNavigate, useParams } from 'react-router-dom'
import { Button } from '../../components/Button'
import { Notice } from '../../components/Notice'
import { ProgressBar } from '../../components/ProgressBar'
import { Steps } from '../../components/Steps'
import { VideoFrame } from '../../components/VideoFrame'
import { DesktopShell } from '../../layouts/DesktopShell'
import { captionFromText } from '../../lib/format'
import { useStore } from '../../lib/store'
import { useProject } from '../../lib/useProject'
import { isActive, renderSteps } from '../../lib/videos'

/** Figma: Laptop v2 / Rendering (9:290). Opens the player when the render finishes. */
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
  if (!project || !video) return <DesktopShell active="new">{null}</DesktopShell>
  if (!render) return <Navigate to={`/videos/${project.id}/script`} replace />

  const background = render.background_id ?? project.background_id ?? defaultBackground
  const labels: Record<string, string> = {
    voice: `Voiced ${project.lines.length} lines`,
    captions: 'Synced captions word by word',
    mix: `Mixing in ${backgroundOf(background).name}`,
    export: 'Exporting 1080 x 1920 MP4',
  }
  const progress = render.progress
  const percent = Math.round(progress * 100)
  const stopped = !isActive(render) && !done
  const firstLine = project.lines[0]?.text

  return (
    <DesktopShell active="new">
      <div className="flex min-h-full flex-col justify-center p-8">
        <div className="flex w-full items-center justify-center gap-20">
          <div className="flex w-[480px] shrink-0 flex-col items-start gap-[18px]">
            <p className="eyebrow text-green-2">{video.title}</p>
            <p className="text-green font-serif text-[120px] leading-[124px] font-bold whitespace-nowrap">{percent}%</p>
            <h1 className="text-ink w-full font-serif text-[32px] leading-[38px] font-semibold">
              {stopped ? (render.status === 'canceled' ? 'Render canceled' : 'The render stopped') : 'Putting your video together'}
            </h1>
            <ProgressBar value={progress} label="Render progress" className="w-full" />
            {stopped ? (
              <Notice>{render.error ?? 'The render was canceled.'}</Notice>
            ) : (
              <p className="text-muted w-full text-[16px] leading-[24px]">
                You can work on another video meanwhile. We’ll let you know when it’s ready.
              </p>
            )}
            {error && <Notice>{error}</Notice>}
            <Steps
              density="desktop"
              items={renderSteps(render).map((step) => ({ ...step, label: labels[step.id] ?? step.id }))}
            />
            <div className="flex gap-[10px]">
              {stopped && <Button onClick={startRender}>Try again</Button>}
              <Button variant="ghost" to={`/videos/${project.id}/script`}>
                Back to script
              </Button>
            </div>
          </div>

          <VideoFrame
            background={background}
            caption={captionFromText(firstLine ?? video.title)}
            captionSize={26}
            avatars={{ size: 39, fontSize: 14 }}
            className="h-[533px] w-[300px] rounded-[18px]"
          >
            {/* "Not rendered yet" veil: covers the part of the frame the render hasn't reached. */}
            <div className="bg-page/82 absolute inset-x-0 bottom-0" style={{ top: `${progress * 100}%` }} />
          </VideoFrame>
        </div>
      </div>
    </DesktopShell>
  )
}
