import { createContext, useContext, useRef, useState, type ReactNode } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Icon } from '../components/Icon'
import type { IconName } from '../components/icons'
import { cn } from '../lib/cn'
import { useStore } from '../lib/store'

type NavKey = 'library' | 'new' | 'engine'

/** Lets any laptop screen open the file picker (sidebar "New video", Library "Make a video" pill). */
const NewVideoContext = createContext<{
  openPicker: () => void
  startFromFile: (file: File) => void
  starting: boolean
  error: string | null
} | null>(null)

export function useNewVideo() {
  const ctx = useContext(NewVideoContext)
  if (!ctx) throw new Error('useNewVideo must be used inside <DesktopShell>')
  return ctx
}

export const ACCEPTED_FILES = 'application/pdf,.pdf,.txt,.md,text/plain,text/markdown'

const navItem = 'flex w-full items-center gap-3 rounded-full px-[14px] py-[11px] text-[15px] whitespace-nowrap'
const navActive = 'bg-green text-page font-semibold'
const navIdle = 'text-muted hover:bg-mint transition-colors'

function NavIcon({ active, on, off }: { active: boolean; on: IconName; off: IconName }) {
  return <Icon name={active ? on : off} />
}

/** Sidebar card: "Engine running" when every local engine is ready, otherwise what's missing. */
function EngineCard() {
  const { health, healthChecked } = useStore()
  const missing = health ? Object.values(health.engines).filter((e) => !e.ok) : []
  const running = health?.ready ?? false
  if (!healthChecked) {
    return (
      <section className="bg-mint rounded-card flex w-full flex-col gap-[6px] p-4">
        <p className="text-muted text-[14px] font-semibold whitespace-nowrap">Checking the engine…</p>
      </section>
    )
  }

  return (
    <section className="bg-mint rounded-card flex w-full flex-col gap-[6px] p-4">
      <p
        className={cn(
          'flex items-center gap-2 text-[14px] font-semibold whitespace-nowrap',
          running ? 'text-green' : 'text-clay-deep',
        )}
      >
        {running ? <Icon name="dotGreen8" /> : <span className="bg-clay size-2 shrink-0 rounded-full" />}
        {!health ? 'Engine offline' : running ? 'Engine running' : 'Engine needs setup'}
      </p>
      <p className="text-muted text-[12px] leading-[17px]">
        {!health
          ? 'Start the server on this laptop: python -m app'
          : running
            ? 'Ollama, Kokoro and Whisper on this laptop. Works offline.'
            : missing.map((e) => e.detail).join('. ')}
      </p>
    </section>
  )
}

/** Figma: Sidebar + Main. The 1440x900 frame border in the mockup is the laptop window, not app UI. */
export function DesktopShell({ active, children }: { active: NavKey; children: ReactNode }) {
  const inputRef = useRef<HTMLInputElement>(null)
  const navigate = useNavigate()
  const store = useStore()
  const [starting, setStarting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // There is no laptop "upload" or "writing script" screen in the design: a picked file
  // starts the script right away (60s, Taglish on) and opens the Workspace.
  const startFromFile = async (file: File) => {
    setStarting(true)
    setError(null)
    try {
      const id = await store.startNewVideo({ file, notes: '' })
      navigate(`/videos/${id}/script`)
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
    } finally {
      setStarting(false)
    }
  }
  const openPicker = () => inputRef.current?.click()

  return (
    <NewVideoContext.Provider value={{ openPicker, startFromFile, starting, error }}>
      <div className="bg-page flex h-full">
        <aside className="border-mint-line bg-card flex h-full w-[240px] shrink-0 flex-col gap-[6px] border-r p-6">
          <Link to="/" className="flex items-center gap-[10px] px-[6px] pt-1 pb-[26px]">
            <span className="relative size-[30px] shrink-0 overflow-clip" aria-hidden>
              <span className="bg-green absolute top-0 left-0 h-[30px] w-[18.6px] rounded-t-[9.3px]" />
              <span className="bg-clay absolute top-[6.6px] left-[15px] h-[23.4px] w-[15px] rounded-t-[7.5px]" />
            </span>
            <span className="text-green font-serif text-[19px] font-bold whitespace-nowrap">Brainrot Study</span>
          </Link>

          <nav className="flex flex-col gap-[6px]" aria-label="Main">
            <Link
              to="/"
              aria-current={active === 'library' ? 'page' : undefined}
              className={cn(navItem, active === 'library' ? navActive : navIdle)}
            >
              <NavIcon active={active === 'library'} on="gridLight18" off="gridMuted18" />
              Library
            </Link>
            <button
              type="button"
              onClick={openPicker}
              disabled={starting}
              aria-current={active === 'new' ? 'page' : undefined}
              className={cn(navItem, active === 'new' ? navActive : navIdle)}
            >
              <NavIcon active={active === 'new'} on="plusLight18" off="plusMuted18" />
              {starting ? 'Starting…' : 'New video'}
            </button>
            {/* The Engine screen is not designed yet, so this is not a link. */}
            <span className={cn(navItem, 'text-muted')} aria-disabled>
              <Icon name="chipMuted18" />
              Engine
            </span>
          </nav>

          <div className="min-h-px flex-1" />

          <EngineCard />
        </aside>

        <main className="h-full min-w-0 flex-1 overflow-y-auto">{children}</main>

        <input
          ref={inputRef}
          type="file"
          accept={ACCEPTED_FILES}
          hidden
          onChange={(e) => {
            const file = e.target.files?.[0]
            if (file) startFromFile(file)
            e.target.value = ''
          }}
        />
      </div>
    </NewVideoContext.Provider>
  )
}
