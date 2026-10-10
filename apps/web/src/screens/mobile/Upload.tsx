import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Button } from '../../components/Button'
import { Icon } from '../../components/Icon'
import { Notice } from '../../components/Notice'
import { Segmented } from '../../components/Segmented'
import { Toggle } from '../../components/Toggle'
import { ACCEPTED_FILES } from '../../layouts/DesktopShell'
import { MobileBottomBar, MobileShell, MobileTitleRow } from '../../layouts/MobileShell'
import { fileSize } from '../../lib/format'
import { keyIdeasForLength, TAGLISH_ENABLED, videoLengths } from '../../lib/options'
import { useStore } from '../../lib/store'

/** Figma: Mobile v2 / Upload (14:99). The design only shows the "file selected" state. */
export function Upload() {
  const navigate = useNavigate()
  const { draft, updateDraft, startNewVideo } = useStore()
  const inputRef = useRef<HTMLInputElement>(null)
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const file = draft.file
  const ready = !!file || draft.notes.trim().length > 0

  async function start() {
    setStarting(true)
    setError(null)
    try {
      const id = await startNewVideo()
      navigate(`/videos/${id}/writing`)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
      setStarting(false)
    }
  }

  return (
    <MobileShell
      headerClassName="gap-[14px] pb-[26px]"
      bodyClassName="gap-[18px]"
      header={
        <>
          <MobileTitleRow backTo="/" title="New video" />
          <p className="text-page w-full font-serif text-[28px] leading-[34px] font-bold">What are we studying?</p>
        </>
      }
      footer={
        <MobileBottomBar className="gap-[10px]">
          <Button className="w-full" onClick={start} disabled={!ready || starting}>
            {starting ? 'Reading your file…' : 'Write the script'}
          </Button>
          <p className="text-muted text-center text-[12px] whitespace-nowrap">
            Runs on your laptop. Nothing leaves your Wi-Fi.
          </p>
        </MobileBottomBar>
      }
    >
      {error && <Notice>{error}</Notice>}

      <section className="bg-card rounded-card shadow-card-sm flex w-full shrink-0 items-center gap-3 p-[14px]">
        <span className="bg-mint flex size-11 shrink-0 items-center justify-center rounded-full">
          <Icon name="file20" />
        </span>
        <div className="flex min-w-0 flex-1 flex-col gap-[3px]">
          <p className="text-ink truncate text-[15px] font-semibold">{file ? file.name : 'No file yet'}</p>
          <p className="text-muted text-[12px] whitespace-nowrap">{file ? fileSize(file.size) : 'PDF, .txt or .md'}</p>
        </div>
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="text-green shrink-0 text-[14px] font-semibold whitespace-nowrap"
        >
          {file ? 'Change' : 'Choose'}
        </button>
        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_FILES}
          hidden
          onChange={(e) => {
            const picked = e.target.files?.[0]
            if (picked) updateDraft({ file: picked })
            e.target.value = ''
          }}
        />
      </section>

      <label className="flex w-full shrink-0 flex-col gap-2">
        <span className="text-ink text-[15px] font-semibold whitespace-nowrap">Or paste notes</span>
        <textarea
          value={draft.notes}
          onChange={(e) => updateDraft({ notes: e.target.value })}
          placeholder="Paste text from your notes app or slides"
          disabled={!!file}
          className="border-mint-line bg-card rounded-input text-ink placeholder:text-muted focus-visible:border-green-2 h-[96px] w-full resize-none border-[1.5px] p-[14px] text-[15px] leading-[21px] outline-none disabled:opacity-60"
        />
        {file && draft.notes.trim() && (
          <span className="text-muted text-[13px]">Using the file. Remove it to use your notes instead.</span>
        )}
      </label>
      {file && (
        <button
          type="button"
          onClick={() => updateDraft({ file: null })}
          className="text-green -mt-2 self-start text-[13px] font-semibold"
        >
          Remove file
        </button>
      )}

      <div className="flex w-full shrink-0 flex-col gap-2">
        <p className="text-ink text-[15px] font-semibold whitespace-nowrap">Video length</p>
        <Segmented
          label="Video length"
          density="mobile"
          options={videoLengths}
          value={draft.lengthSec}
          onChange={(lengthSec) => updateDraft({ lengthSec })}
        />
        <p className="text-muted text-[13px] whitespace-nowrap">
          {draft.lengthSec}s covers about {keyIdeasForLength[draft.lengthSec]} key ideas.
        </p>
      </div>

      {TAGLISH_ENABLED && (
        <div className="bg-mint rounded-card flex w-full shrink-0 items-center gap-3 p-4">
          <div className="flex min-w-0 flex-1 flex-col gap-[2px] whitespace-nowrap">
            <p className="text-ink text-[15px] font-semibold">Taglish mode</p>
            <p className="text-muted text-[13px]">English and Filipino jokes</p>
          </div>
          <Toggle label="Taglish mode" checked={draft.taglish} onChange={(taglish) => updateDraft({ taglish })} />
        </div>
      )}
    </MobileShell>
  )
}
