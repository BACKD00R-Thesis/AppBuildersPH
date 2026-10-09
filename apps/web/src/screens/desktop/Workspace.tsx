import { useNavigate, useParams } from 'react-router-dom'
import { Avatar } from '../../components/Avatar'
import { BackButton } from '../../components/BackButton'
import { Button } from '../../components/Button'
import { Icon } from '../../components/Icon'
import { Notice, NoticeAction } from '../../components/Notice'
import { ScriptSteps, useSecondsLeft } from '../../components/ScriptProgress'
import { ScriptList, useScriptEditing } from '../../components/ScriptList'
import { Segmented } from '../../components/Segmented'
import { Toggle } from '../../components/Toggle'
import { VideoFrame } from '../../components/VideoFrame'
import { DesktopShell } from '../../layouts/DesktopShell'
import { usePlaying } from '../../lib/audio'
import { cn } from '../../lib/cn'
import { captionFromText } from '../../lib/format'
import { captionStyles } from '../../lib/options'
import { speakerIds, speakerOf } from '../../lib/speakers'
import { useStore } from '../../lib/store'
import { useProject } from '../../lib/useProject'
import { scriptSeconds } from '../../lib/videos'

/** Figma: Laptop v2 / Workspace (9:116). Script, live preview and style in one screen. */
export function Workspace() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { backgrounds, defaultBackground, playVoiceSample } = useStore()
  const handle = useProject(id)
  const { project, video, error, setError, notFound, updateStyle, regenerate, startRender } = handle
  const editing = useScriptEditing(handle)
  const secondsLeft = useSecondsLeft(project)
  const playing = usePlaying()

  if (notFound) {
    return (
      <DesktopShell active="library">
        <div className="p-8">
          <Notice action={<NoticeAction onClick={() => navigate('/')}>Back to library</NoticeAction>}>
            This video doesn’t exist anymore.
          </Notice>
        </div>
      </DesktopShell>
    )
  }
  if (!project || !video) return <DesktopShell active="new">{null}</DesktopShell>

  const writing = project.status === 'generating' || project.status === 'ready'
  const failed = project.status === 'failed' && editing.lines.length === 0
  const background = project.background_id ?? defaultBackground
  const firstLine = editing.lines.find((l) => l.text.trim())?.text
  const meta = [
    project.source_name ?? 'Pasted notes',
    writing ? secondsLeft.toLowerCase() : `${editing.lines.length} lines`,
    !writing && `about ${scriptSeconds(editing.lines)}s`,
  ]
    .filter(Boolean)
    .join(', ')

  const onRegenerate = () => {
    if (editing.lines.length && !window.confirm('Write a new script? This replaces every line, including your edits.')) return
    regenerate()
  }

  const onRender = async () => {
    if (!(await editing.save())) return
    if (await startRender()) navigate(`/videos/${project.id}/rendering`)
  }

  return (
    <DesktopShell active="new">
      <div className="flex h-full min-h-[850px] flex-col gap-5 px-8 py-6">
        <header className="bg-green flex w-full shrink-0 items-center gap-4 rounded-[24px] px-7 py-[22px]">
          <BackButton to="/" label="Back to library" />
          <div className="flex min-w-0 flex-1 flex-col gap-1 whitespace-nowrap">
            <p className="eyebrow text-on-green">{video.subject}</p>
            <h1 className="text-page truncate font-serif text-[30px] leading-[36px] font-bold">{video.title}</h1>
            <p className="text-on-green text-[14px]">{meta}</p>
          </div>
        </header>

        {error && (
          <Notice action={<NoticeAction onClick={() => setError(null)}>Dismiss</NoticeAction>}>{error}</Notice>
        )}

        <div className="flex min-h-0 w-full flex-1 items-start gap-6">
          {/* Script. Negative margin + padding keeps card shadows from being clipped by the scroll area. */}
          <section className="-mx-6 -mb-6 flex h-[calc(100%+24px)] min-w-0 flex-1 flex-col gap-3 overflow-y-auto px-6 pb-6">
            <div className="flex w-full shrink-0 items-center justify-between">
              <h2 className="text-ink font-serif text-[22px] font-semibold">Script</h2>
              <Button variant="ghost" onClick={onRegenerate} disabled={writing}>
                {writing ? 'Writing…' : 'Regenerate'}
              </Button>
            </div>

            {writing ? (
              <ScriptSteps project={project} density="desktop" />
            ) : failed ? (
              <Notice action={<NoticeAction onClick={regenerate}>Try again</NoticeAction>}>
                {project.error ?? 'The script couldn’t be written.'}
              </Notice>
            ) : (
              <>
                {project.error && (
                  <Notice action={<NoticeAction onClick={regenerate}>Try again</NoticeAction>}>
                    Couldn’t write a new script: {project.error}
                  </Notice>
                )}
                <ScriptList editing={editing} density="desktop" editHint="Enter to save" />
                <Button variant="secondary" className="shrink-0 self-start" onClick={editing.addAndEdit}>
                  Add line
                </Button>
              </>
            )}
          </section>

          <section className="flex w-[280px] shrink-0 flex-col items-center gap-3">
            <h2 className="text-ink w-full font-serif text-[22px] font-semibold">Preview</h2>
            <VideoFrame
              background={background}
              caption={captionFromText(firstLine ?? video.title)}
              captionSize={25}
              avatars={{ size: 36, fontSize: 13 }}
              className="h-[498px] w-[280px] rounded-[18px]"
            />
            <p className="text-muted text-[13px] whitespace-nowrap">Updates as you edit</p>
          </section>

          <section className="bg-card rounded-card shadow-card flex h-full w-[300px] shrink-0 flex-col gap-5 p-[22px]">
            <h2 className="text-ink font-serif text-[22px] font-semibold">Style</h2>

            <div className="flex w-full flex-col gap-3">
              <h3 className="eyebrow text-green-2">Voices</h3>
              {speakerIds.map((speaker) => (
                <div key={speaker} className="flex w-full items-center gap-[10px]">
                  <Avatar speaker={speaker} size={34} fontSize={12} />
                  <div className="flex min-w-0 flex-1 flex-col gap-[2px] whitespace-nowrap">
                    <p className="text-ink text-[15px] font-semibold">{speakerOf(speaker).name}</p>
                    <p className="text-muted text-[13px]">{speakerOf(speaker).vibe}</p>
                  </div>
                  <button
                    type="button"
                    onClick={() => playVoiceSample(speaker).catch((err) => setError(String(err?.message ?? err)))}
                    aria-label={`Hear ${speakerOf(speaker).name}`}
                    aria-pressed={playing === `sample:${speaker}`}
                    className={cn(
                      'bg-mint flex size-8 shrink-0 items-center justify-center rounded-full',
                      playing === `sample:${speaker}` && 'ring-green-2 ring-2',
                    )}
                  >
                    <Icon name="play13" />
                  </button>
                </div>
              ))}
            </div>

            <div className="flex w-full flex-col gap-[10px]">
              <h3 className="eyebrow text-green-2">Background</h3>
              <div role="radiogroup" aria-label="Background" className="flex w-full flex-wrap gap-3">
                {backgrounds.map((bg) => {
                  const selected = background === bg.id
                  return (
                    <button
                      key={bg.id}
                      type="button"
                      role="radio"
                      aria-checked={selected}
                      onClick={() => updateStyle({ background_id: bg.id })}
                      className="flex flex-col items-start gap-[6px]"
                    >
                      <span
                        className={cn('block h-[70px] w-[122px] rounded-[14px]', selected && 'ring-green ring-3')}
                        style={{ backgroundImage: `linear-gradient(to bottom, ${bg.from}, ${bg.to})` }}
                      />
                      <span
                        className={cn(
                          'text-[13px] whitespace-nowrap',
                          selected ? 'text-ink font-semibold' : 'text-muted',
                        )}
                      >
                        {bg.name}
                      </span>
                    </button>
                  )
                })}
              </div>
            </div>

            <div className="flex w-full flex-col gap-[10px]">
              <h3 className="eyebrow text-green-2">Captions</h3>
              <Segmented
                label="Captions"
                density="desktop"
                options={captionStyles}
                value={project.caption_style}
                onChange={(caption_style) => updateStyle({ caption_style })}
              />
            </div>

            <div className="flex w-full items-center gap-3">
              <div className="flex min-w-0 flex-1 flex-col gap-[2px] whitespace-nowrap">
                <p className="text-ink text-[15px] font-semibold">Taglish mode</p>
                <p className="text-muted text-[13px]">
                  {/* Language is decided when the script is written. */}
                  English and Filipino jokes
                </p>
              </div>
              <Toggle label="Taglish mode" checked={project.taglish} onChange={(taglish) => updateStyle({ taglish })} />
            </div>

            <div className="min-h-px flex-1" />

            <Button className="w-full shrink-0" onClick={onRender} disabled={writing || failed || editing.saving}>
              Render video
            </Button>
          </section>
        </div>
      </div>
    </DesktopShell>
  )
}
