import { useState } from 'react'
import { api, type Render } from '../lib/api'
import { cn } from '../lib/cn'

/** Playback position for the custom progress row under the video. */
export function usePlayback() {
  const [position, setPosition] = useState(0)
  const [duration, setDuration] = useState(0)
  return {
    position,
    duration,
    bind: {
      onTimeUpdate: (e: React.SyntheticEvent<HTMLVideoElement>) => setPosition(e.currentTarget.currentTime),
      onLoadedMetadata: (e: React.SyntheticEvent<HTMLVideoElement>) => setDuration(e.currentTarget.duration),
    },
  }
}

/** The rendered MP4, replacing the design's VideoFrame placeholder on the player screens. */
export function VideoPlayer({
  render,
  className,
  bind,
}: {
  render: Render
  className?: string
  bind: ReturnType<typeof usePlayback>['bind']
}) {
  return (
    <video
      key={render.id}
      src={api.videoUrl(render)}
      controls
      playsInline
      autoPlay
      className={cn('bg-video shrink-0 object-contain', className)}
      {...bind}
    />
  )
}

/** Download, or share the MP4 file where the browser supports it (phones), else download. */
export async function shareVideo(render: Render, title: string): Promise<'shared' | 'downloaded'> {
  const response = await fetch(api.videoUrl(render))
  const blob = await response.blob()
  const file = new File([blob], `${title}.mp4`, { type: 'video/mp4' })
  if (navigator.canShare?.({ files: [file] })) {
    await navigator.share({ files: [file], title })
    return 'shared'
  }
  downloadVideo(render)
  return 'downloaded'
}

export function downloadVideo(render: Render): void {
  const a = document.createElement('a')
  a.href = api.videoUrl(render, true)
  a.download = ''
  document.body.appendChild(a)
  a.click()
  a.remove()
}
