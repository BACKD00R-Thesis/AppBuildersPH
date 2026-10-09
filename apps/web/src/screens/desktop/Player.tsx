import { useState } from 'react'
import { Link, Navigate, useParams } from 'react-router-dom'
import { Button } from '../../components/Button'
import { KeyIdeas } from '../../components/KeyIdeas'
import { Notice } from '../../components/Notice'
import { ProgressBar } from '../../components/ProgressBar'
import { downloadVideo, usePlayback, VideoPlayer } from '../../components/VideoPlayer'
import { DesktopShell } from '../../layouts/DesktopShell'
import { api } from '../../lib/api'
import { clock } from '../../lib/format'
import { useProject } from '../../lib/useProject'
import { projectHref } from '../../lib/videos'

/** Figma: Laptop v2 / Player (9:360) */
export function Player() {
  const { id } = useParams()
  const { project, video, notFound } = useProject(id)
  const playback = usePlayback()
  const [error, setError] = useState<string | null>(null)

  if (notFound) return <Navigate to="/" replace />
  if (!project || !video) return <DesktopShell active="library">{null}</DesktopShell>
  const render = project.video
  if (!render) return <Navigate to={projectHref(project)} replace />

  const duration = playback.duration || render.duration_s || video.durationSec

  return (
    <DesktopShell active="library">
      <div className="flex min-h-full flex-col justify-center p-8">
        <div className="flex w-full items-center justify-center gap-8 min-[1300px]:gap-16">
          {/* 405x720 in Figma; shrinks on short screens. */}
          <VideoPlayer
            render={render}
            bind={playback.bind}
            className="aspect-[9/16] h-[min(720px,calc(100dvh-64px))] min-h-[480px] rounded-[24px]"
          />

          <div className="flex max-w-[460px] min-w-[340px] flex-1 flex-col items-start gap-[22px]">
            <div className="flex w-full flex-col items-start gap-2">
              <p className="eyebrow text-green-2">{video.subject}</p>
              <h1 className="text-green w-full font-serif text-[38px] leading-[44px] font-bold">{video.title}</h1>
              <p className="text-muted text-[15px] whitespace-nowrap">Saved on this laptop</p>
            </div>

            <div className="text-muted flex w-full items-center gap-[10px] text-[13px] whitespace-nowrap">
              <span>{clock(playback.position)}</span>
              <ProgressBar value={duration ? playback.position / duration : 0} label="Playback" className="min-w-0 flex-1" />
              <span>{clock(duration)}</span>
            </div>

            <div className="flex w-full gap-[10px]">
              <Button className="min-w-0 flex-1" onClick={() => downloadVideo(render)}>
                Download MP4
              </Button>
              <Button
                variant="secondary"
                className="min-w-0 flex-1"
                onClick={() => api.revealRender(render.id).catch((err) => setError(err.message))}
              >
                Open folder
              </Button>
            </div>
            {error && <Notice>{error}</Notice>}

            {project.key_ideas.length > 0 && <KeyIdeas ideas={project.key_ideas} density="desktop" />}

            <Link to={`/videos/${project.id}/script`} className="text-green text-[15px] font-semibold whitespace-nowrap">
              Edit script
            </Link>
          </div>
        </div>
      </div>
    </DesktopShell>
  )
}
