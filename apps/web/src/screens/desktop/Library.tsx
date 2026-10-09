import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Icon } from '../../components/Icon'
import { Notice, NoticeAction } from '../../components/Notice'
import { VideoFrame } from '../../components/VideoFrame'
import { DesktopShell, useNewVideo } from '../../layouts/DesktopShell'
import { cn } from '../../lib/cn'
import { useStore } from '../../lib/store'

/** Figma: Laptop v2 / Library (9:12) */
export function Library() {
  return (
    <DesktopShell active="library">
      <LibraryMain />
    </DesktopShell>
  )
}

function LibraryMain() {
  const { videos, videosLoaded, videosError, reloadVideos, userName } = useStore()
  const { error } = useNewVideo()

  return (
    <div className="flex flex-col gap-7 p-8">
      <section className="bg-green relative h-[290px] w-full shrink-0 overflow-clip rounded-[28px]">
        {/* Arches: headers and empty states only, never behind text. */}
        <div className="bg-clay absolute top-[48px] right-[216px] h-[300px] w-[120px] rounded-t-[60px]" />
        <div className="bg-clay-deep absolute top-[65px] right-[233px] h-[300px] w-[86px] rounded-t-[43px]" />
        <div className="bg-clay-2 absolute top-[100px] right-[102px] h-[260px] w-[104px] rounded-t-[52px]" />
        <div className="bg-clay-2-deep absolute top-[115px] right-[117px] h-[260px] w-[74px] rounded-t-[37px]" />
        <div className="bg-green-2 absolute top-[150px] right-[22px] h-[200px] w-[70px] rounded-t-[35px]" />

        <h1 className="text-page absolute top-[40px] left-[44px] font-serif text-[52px] leading-[58px] font-bold whitespace-nowrap">
          {userName ? `Kumusta, ${userName}!` : 'Kumusta!'}
        </h1>
        <p className="text-on-green absolute top-[106px] left-[44px] text-[17px] whitespace-nowrap">
          What are we studying tonight?
        </p>
        <MakeVideoPill />
      </section>

      {error && <Notice>{error}</Notice>}
      {videosError && (
        <Notice action={<NoticeAction onClick={reloadVideos}>Retry</NoticeAction>}>{videosError}</Notice>
      )}

      <div className="flex w-full items-center justify-between whitespace-nowrap">
        <h2 className="text-ink font-serif text-[28px] font-semibold">Your videos</h2>
        <p className="text-muted text-[14px]">
          {videos.length} {videos.length === 1 ? 'video' : 'videos'}
        </p>
      </div>

      {videosLoaded && videos.length === 0 && !videosError && (
        <Notice tone="info">No videos yet. Drop a PDF on the pill above to make your first one.</Notice>
      )}

      <ul className="grid w-full grid-cols-[repeat(auto-fill,minmax(200px,1fr))] gap-5">
        {videos.map((video) => (
          <li key={video.id}>
            <Link to={video.href} className="bg-card rounded-card shadow-card flex flex-col gap-[10px] p-3">
              <VideoFrame
                background={video.background}
                caption={video.caption}
                captionSize={17}
                captionTop="32%"
                className="h-[236px] w-full rounded-[14px]"
              />
              <p className="text-ink w-full text-[15px] font-bold [overflow-wrap:anywhere]">{video.title}</p>
              <div className="flex w-full items-center justify-between gap-2 whitespace-nowrap">
                <span className="eyebrow text-green-2 min-w-0 truncate">{video.subject}</span>
                <span className="text-muted text-[13px]">{video.progressLabel ?? `${video.durationSec}s`}</span>
              </div>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}

/** Click to pick a file, or drop one on it. */
function MakeVideoPill() {
  const { openPicker, startFromFile, starting } = useNewVideo()
  const [over, setOver] = useState(false)

  return (
    <button
      type="button"
      onClick={openPicker}
      disabled={starting}
      onDragOver={(e) => {
        e.preventDefault()
        setOver(true)
      }}
      onDragLeave={() => setOver(false)}
      onDrop={(e) => {
        e.preventDefault()
        setOver(false)
        const file = e.dataTransfer.files[0]
        if (file) startFromFile(file)
      }}
      className={cn(
        'bg-card shadow-card absolute top-[176px] left-[44px] flex items-center gap-[14px] rounded-full py-[14px] pr-[14px] pl-[22px] text-left',
        over && 'ring-mustard ring-3',
      )}
    >
      <Icon name="sparkle22" />
      <span className="flex flex-col gap-[2px] whitespace-nowrap">
        <span className="text-ink text-[17px] font-bold">
          {starting ? 'Reading your file…' : 'Make a video from a PDF'}
        </span>
        <span className="text-muted text-[13px]">Drop slides, notes or a chapter here</span>
      </span>
      <span className="h-px w-[200px] shrink-0" />
      <span className="bg-green flex size-[46px] shrink-0 items-center justify-center rounded-full">
        <Icon name="plusLight22" />
      </span>
    </button>
  )
}
