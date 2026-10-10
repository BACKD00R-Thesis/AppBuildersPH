import { useRef, useState } from 'react'
import { Navigate, useNavigate, useParams } from 'react-router-dom'
import { Avatar } from '../../components/Avatar'
import { Button } from '../../components/Button'
import { Icon } from '../../components/Icon'
import { Notice, NoticeAction } from '../../components/Notice'
import { Segmented } from '../../components/Segmented'
import { VoiceStylePicker } from '../../components/VoiceStylePicker'
import { VideoFrame } from '../../components/VideoFrame'
import { MobileBottomBar, MobileShell, MobileTitleRow } from '../../layouts/MobileShell'
import { usePlaying } from '../../lib/audio'
import { cn } from '../../lib/cn'
import { captionFromText } from '../../lib/format'
import { captionStyles } from '../../lib/options'
import { speakerIds, speakerOf } from '../../lib/speakers'
import { useStore } from '../../lib/store'
import { useProject } from '../../lib/useProject'

/** Figma: Mobile v2 / Style (14:270) */
export function Style() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { backgrounds, defaultBackground, playVoiceSample, uploadBackground, background: backgroundOf } = useStore()
  const { project, video, notFound, updateStyle, startRender, error, setError } = useProject(id)
  const playing = usePlaying()
  const backgroundInput = useRef<HTMLInputElement | null>(null)
  const [backgroundUploading, setBackgroundUploading] = useState(false)

  if (notFound) return <Navigate to="/" replace />
  if (!project || !video) return null

  const background = project.background_id ?? defaultBackground
  const firstLine = project.lines[0]?.text

  const onBackgroundFile = async (file: File | null) => {
    if (!file) return
    setBackgroundUploading(true)
    setError(null)
    try {
      const uploaded = await uploadBackground(file)
      await updateStyle({ background_id: uploaded.id })
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setBackgroundUploading(false)
      if (backgroundInput.current) backgroundInput.current.value = ''
    }
  }

  return (
    <MobileShell
      headerClassName="gap-[14px] pb-5"
      bodyClassName="gap-[18px]"
      header={<MobileTitleRow backTo={`/videos/${project.id}/script`} title="Style" />}
      footer={
        <MobileBottomBar className="gap-[10px]">
          <Button
            className="w-full"
            disabled={project.lines.length === 0}
            onClick={async () => {
              if (await startRender()) navigate(`/videos/${project.id}/rendering`)
            }}
          >
            Render video
          </Button>
          <p className="text-muted text-center text-[12px] whitespace-nowrap">
            {project.voice_style === 'expressive'
              ? 'A few minutes longer with Expressive voices'
              : 'About 2 minutes on your laptop'}
          </p>
        </MobileBottomBar>
      }
    >
      {error && (
        <Notice action={<NoticeAction onClick={() => setError(null)}>OK</NoticeAction>}>{error}</Notice>
      )}

      <div className="flex w-full shrink-0 items-start gap-[14px]">
        <VideoFrame
          background={background}
          caption={captionFromText(firstLine ?? video.title)}
          captionSize={16}
          cast
          className="h-[267px] w-[150px] rounded-[16px]"
        />
        <div className="flex min-w-0 flex-1 flex-col gap-[10px]">
          <h2 className="eyebrow text-green-2">Voices</h2>
          {speakerIds.map((speaker) => {
            const titoBoy = speaker === 'tito-boy'
            const isPlaying = playing === `sample:${speaker}`
            return (
              <div
                key={speaker}
                className={cn(
                  'rounded-card flex w-full flex-col gap-[10px] p-[14px]',
                  titoBoy ? 'bg-mint' : 'bg-card shadow-card-sm',
                )}
              >
                <div className="flex items-center gap-2">
                  <Avatar speaker={speaker} size={28} fontSize={10} />
                  <div className="flex flex-col gap-px whitespace-nowrap">
                    <p className="text-ink text-[14px] font-semibold">{speakerOf(speaker).name}</p>
                    <p className="text-muted text-[12px]">{speakerOf(speaker).vibe}</p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={() => playVoiceSample(speaker, project.voice_style).catch((err) => setError(String(err?.message ?? err)))}
                  aria-pressed={isPlaying}
                  className="text-green flex items-center gap-2 self-start text-[13px] whitespace-nowrap"
                >
                  <span
                    className={cn(
                      'flex size-7 shrink-0 items-center justify-center rounded-full',
                      titoBoy ? 'bg-card' : 'bg-mint',
                    )}
                  >
                    <Icon name="play12" />
                  </span>
                  {isPlaying ? 'Playing…' : 'Hear sample'}
                </button>
              </div>
            )
          })}
        </div>
      </div>

      <div className="flex w-full shrink-0 flex-col gap-[10px]">
        <h2 className="eyebrow text-green-2">Voice style</h2>
        <VoiceStylePicker value={project.voice_style} onChange={(voice_style) => updateStyle({ voice_style })} />
      </div>

      <div className="flex w-full shrink-0 flex-col gap-[10px]">
        <h2 className="eyebrow text-green-2">Background</h2>
        <div role="radiogroup" aria-label="Background" className="-mx-1 flex gap-[10px] overflow-x-auto px-1 pb-1">
          {backgrounds.map((bg) => {
            const selected = background === bg.id
            const preview = backgroundOf(bg.id).previewUrl
            return (
              <button
                key={bg.id}
                type="button"
                role="radio"
                aria-checked={selected}
                onClick={() => updateStyle({ background_id: bg.id })}
                className="flex w-[76px] min-w-0 shrink flex-col items-start gap-[6px]"
              >
                <span
                  className={cn('relative block aspect-[76/96] w-full overflow-hidden rounded-[14px]', selected && 'ring-green ring-3')}
                  style={{ backgroundImage: `linear-gradient(to bottom, ${bg.from}, ${bg.to})` }}
                >
                  {preview && (
                    <video
                      src={preview}
                      className="absolute inset-0 size-full object-cover"
                      autoPlay
                      muted
                      loop
                      playsInline
                    />
                  )}
                </span>
                <span className={cn('w-full text-[12px] leading-[14px] break-all', selected ? 'text-ink font-semibold' : 'text-muted')}>
                  {bg.short_name}
                </span>
              </button>
            )
          })}
        </div>
        <input
          ref={backgroundInput}
          type="file"
          accept="video/mp4,video/quicktime,video/webm,.mp4,.mov,.m4v,.webm"
          className="hidden"
          onChange={(event) => onBackgroundFile(event.currentTarget.files?.[0] ?? null)}
        />
        <Button
          variant="ghost"
          className="w-full px-4 py-[12px]"
          disabled={backgroundUploading}
          onClick={() => backgroundInput.current?.click()}
        >
          {backgroundUploading ? 'Adding…' : 'Add your own background'}
        </Button>
      </div>

      <div className="flex w-full shrink-0 flex-col gap-[10px]">
        <h2 className="eyebrow text-green-2">Captions</h2>
        <Segmented
          label="Captions"
          density="mobile"
          options={captionStyles}
          value={project.caption_style}
          onChange={(caption_style) => updateStyle({ caption_style })}
        />
      </div>
    </MobileShell>
  )
}
