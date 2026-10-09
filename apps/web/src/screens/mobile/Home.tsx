import { Link } from 'react-router-dom'
import { Button } from '../../components/Button'
import { Icon } from '../../components/Icon'
import { Notice, NoticeAction } from '../../components/Notice'
import { VideoFrame } from '../../components/VideoFrame'
import { MobileShell } from '../../layouts/MobileShell'
import { TabBar } from '../../layouts/TabBar'
import { shortCaption } from '../../lib/format'
import { useStore } from '../../lib/store'

const WEEK_MS = 7 * 24 * 60 * 60 * 1000

/** Figma: Mobile v2 / Home (14:12) */
export function Home() {
  const { videos, videosLoaded, videosError, reloadVideos, userName } = useStore()
  // The green card features the newest finished video; everything else is listed below it.
  const latest = videos.find((v) => v.hasVideo)
  const rest = videos.filter((v) => v !== latest)
  const thisWeek = videos.filter((v) => v.madeAt && Date.now() - new Date(v.madeAt).getTime() < WEEK_MS).length

  return (
    <MobileShell
      headerClassName="gap-3 pb-[26px]"
      bodyClassName="gap-4"
      footer={<TabBar />}
      header={
        <>
          {/* Arches sit behind the pill, anchored to the right edge. */}
          <div className="bg-clay absolute top-[2px] right-[70px] h-[200px] w-[70px] rounded-t-[35px]" />
          <div className="bg-clay-deep absolute top-[13px] right-[81px] h-[200px] w-[48px] rounded-t-[24px]" />
          <div className="bg-clay-2 absolute top-[40px] right-[10px] h-[180px] w-[62px] rounded-t-[31px]" />
          <div className="bg-clay-2-deep absolute top-[49px] right-[19px] h-[180px] w-[44px] rounded-t-[22px]" />

          <h1 className="text-page relative font-serif text-[36px] leading-[40px] font-bold whitespace-nowrap">
            {userName ? (
              <>
                Kumusta,
                <br />
                {userName}!
              </>
            ) : (
              'Kumusta!'
            )}
          </h1>
          <p className="bg-green-2 text-page relative self-start rounded-full px-3 py-[6px] text-[12px] font-semibold whitespace-nowrap">
            {thisWeek === 1 ? '1 video' : `${thisWeek} videos`} this week
          </p>
          <Link
            to="/new"
            className="bg-card shadow-card-sm relative flex w-full items-center gap-3 rounded-full py-3 pr-3 pl-[18px]"
          >
            <Icon name="sparkle20" />
            <span className="flex min-w-0 flex-1 flex-col gap-[2px] whitespace-nowrap">
              <span className="text-ink text-[16px] font-bold">Make a video</span>
              <span className="text-muted text-[12px]">From a PDF, slides or notes</span>
            </span>
            <span className="bg-green flex size-10 shrink-0 items-center justify-center rounded-full">
              <Icon name="plusLight20" />
            </span>
          </Link>
        </>
      }
    >
      {videosError && (
        <Notice action={<NoticeAction onClick={reloadVideos}>Retry</NoticeAction>}>{videosError}</Notice>
      )}

      {latest && (
        <section className="bg-green rounded-card flex w-full shrink-0 flex-col gap-[10px] p-[18px]">
          <div className="flex w-full items-center justify-between">
            <p className="eyebrow text-on-green">{latest.subject}</p>
            {latest.isNew && (
              <span className="bg-mustard text-ink rounded-[8px] px-[10px] py-1 text-[12px] font-bold whitespace-nowrap">
                New
              </span>
            )}
          </div>
          <h2 className="text-page w-full font-serif text-[22px] font-bold">{latest.title}</h2>
          <p className="text-on-green text-[13px] whitespace-nowrap">
            {latest.lineCount} lines, {latest.durationSec} seconds
          </p>
          <Button variant="secondary" to={`/videos/${latest.id}`} className="w-full">
            Watch
          </Button>
        </section>
      )}

      <div className="flex w-full shrink-0 items-center justify-between whitespace-nowrap">
        <h2 className="text-ink font-serif text-[22px] font-semibold">Your videos</h2>
        <p className="text-muted text-[14px]">{videos.length}</p>
      </div>

      {videosLoaded && videos.length === 0 && !videosError && (
        <Notice tone="info">No videos yet. Tap “Make a video” to turn a PDF or your notes into one.</Notice>
      )}

      <ul className="flex w-full flex-col gap-4">
        {rest.map((video) => (
          <li key={video.id}>
            <Link
              to={video.href}
              className="bg-mint flex w-full items-center gap-3 rounded-[16px] py-[10px] pr-[14px] pl-[10px]"
            >
              <VideoFrame
                background={video.background}
                caption={shortCaption(video.caption)}
                captionSize={7}
                strokeWidth={2}
                captionTop="30%"
                className="h-[52px] w-[40px] rounded-[10px]"
              />
              <span className="flex min-w-0 flex-1 flex-col gap-[2px] whitespace-nowrap">
                <span className="text-ink truncate text-[15px] font-semibold">{video.title}</span>
                <span className="text-muted truncate text-[12px]">
                  {video.subject}, {video.progressLabel ?? `${video.durationSec}s`}
                </span>
              </span>
              <Icon name="chev18" />
            </Link>
          </li>
        ))}
      </ul>
    </MobileShell>
  )
}
