import type { ReactNode } from 'react'
import { Navigate, Route, Routes, useParams } from 'react-router-dom'
import { useIsDesktop } from './lib/useIsDesktop'
import { Library } from './screens/desktop/Library'
import { Player as DesktopPlayer } from './screens/desktop/Player'
import { Rendering as DesktopRendering } from './screens/desktop/Rendering'
import { Workspace } from './screens/desktop/Workspace'
import { Home } from './screens/mobile/Home'
import { Player as MobilePlayer } from './screens/mobile/Player'
import { Rendering as MobileRendering } from './screens/mobile/Rendering'
import { ScriptEditor } from './screens/mobile/ScriptEditor'
import { Style } from './screens/mobile/Style'
import { Upload } from './screens/mobile/Upload'
import { WritingScript } from './screens/mobile/WritingScript'
import { ScreensIndex } from './screens/ScreensIndex'

/** One URL per step. Each renders the laptop or the mobile design depending on window width. */
function Responsive({ desktop, mobile }: { desktop: ReactNode; mobile: ReactNode }) {
  return useIsDesktop() ? desktop : mobile
}

/** Laptop has no separate screen for this step: the Workspace covers it. */
function ToWorkspace() {
  const { id } = useParams()
  return <Navigate to={`/videos/${id}/script`} replace />
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Responsive desktop={<Library />} mobile={<Home />} />} />
      <Route path="/new" element={<Responsive desktop={<Navigate to="/" replace />} mobile={<Upload />} />} />
      <Route
        path="/videos/:id/writing"
        element={<Responsive desktop={<ToWorkspace />} mobile={<WritingScript />} />}
      />
      <Route path="/videos/:id/script" element={<Responsive desktop={<Workspace />} mobile={<ScriptEditor />} />} />
      <Route path="/videos/:id/style" element={<Responsive desktop={<ToWorkspace />} mobile={<Style />} />} />
      <Route
        path="/videos/:id/rendering"
        element={<Responsive desktop={<DesktopRendering />} mobile={<MobileRendering />} />}
      />
      <Route path="/videos/:id" element={<Responsive desktop={<DesktopPlayer />} mobile={<MobilePlayer />} />} />
      <Route path="/_screens" element={<ScreensIndex />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}
