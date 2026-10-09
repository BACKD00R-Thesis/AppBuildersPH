import { useState } from 'react'
import { Link, Navigate, useParams } from 'react-router-dom'
import { Button } from '../../components/Button'
import { KeyIdeas } from '../../components/KeyIdeas'
import { Notice } from '../../components/Notice'
import { ProgressBar } from '../../components/ProgressBar'
import { downloadVideo, shareVideo, usePlayback, VideoPlayer } from '../../components/VideoPlayer'
import { clock } from '../../lib/format'
import { useProject } from '../../lib/useProject'
import { projectHref } from '../../lib/videos'

/**
 * Figma: Mobile v2 / Player (14:387). Dark top with the video, then a sheet.
 * The design has no back control on this screen; the browser back button is the way out.
 */
export function Player() {
  const { id } = useParams()
  const { project, video, notFound } = useProject(id)
  const playback = usePlayback()
  const [sharing, setSharing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (notFound) return <Navigate to="/" replace />
  if (!project || !video) return <div className="bg-video mx-auto h-full w-full max-w-[480px]" />
  const render = project.video
  if (!render) return <Navigate to={projectHref(project)} replace />

  const duration = playback.duration || render.duration_s || video.durationSec

  return (
    <div className="bg-video mx-auto flex h-full w-full max-w-[480px] flex-col pt-[env(safe-area-inset-top)]">
      <VideoPlayer render={render} bind={playback.bind} className="h-[400px] w-full" />

      <main className="bg-page flex min-h-0 w-full flex-1 flex-col gap-[14px] overflow-y-auto rounded-t-[28px] px-5 pt-[18px] pb-[14px]">
        <div className="flex w-full shrink-0 justify-center" aria-hidden>
          <div className="bg-mint-line h-[5px] w-10 rounded-[3px]" />
        </div>

        <div className="flex w-full shrink-0 flex-col gap-1 font-bold">
          <p className="eyebrow text-green-2">{video.subject}</p>
          <h1 className="text-green w-full font-serif text-[22px] leading-[28px]">{video.title}</h1>
        </div>

        <div className="text-muted flex w-full shrink-0 items-center gap-[10px] text-[12px] whitespace-nowrap">
          <span>{clock(playback.position)}</span>
          <ProgressBar value={duration ? playback.position / duration : 0} label="Playback" className="min-w-0 flex-1" />
          <span>{clock(duration)}</span>
        </div>

        <div className="flex w-full shrink-0 gap-[10px]">
          <Button className="min-w-0 flex-1" onClick={() => downloadVideo(render)}>
            Download
          </Button>
          <Button
            variant="secondary"
            className="min-w-0 flex-1"
            disabled={sharing}
            onClick={async () => {
              setSharing(true)
              setError(null)
              try {
                await shareVideo(render, video.title)
              } catch (err) {
                // Closing the share sheet rejects with AbortError; that's not a failure.
                if (!(err instanceof DOMException && err.name === 'AbortError')) setError('Couldn’t share the video.')
              } finally {
                setSharing(false)
              }
            }}
          >
            {sharing ? 'Preparing…' : 'Share'}
          </Button>
        </div>
        {error && <Notice>{error}</Notice>}

        {project.key_ideas.length > 0 && (
          <div className="w-full shrink-0">
            <KeyIdeas ideas={project.key_ideas} density="mobile" />
          </div>
        )}

        <Link to={`/videos/${project.id}/script`} className="text-green shrink-0 self-center text-[14px] font-semibold">
          Edit script
        </Link>
      </main>
    </div>
  )
}
