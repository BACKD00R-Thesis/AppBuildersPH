import { Link } from 'react-router-dom'
import { useStore } from '../lib/store'

/** Dev aid: every screen in one list, for the newest video. Open at /_screens. Safe to delete. */
export function ScreensIndex() {
  const { videos } = useStore()
  const id = videos[0]?.id

  const routes: { path: string; laptop: string; mobile: string }[] = [
    { path: '/', laptop: 'Library', mobile: 'Home' },
    { path: '/new', laptop: 'not designed (redirects to Library)', mobile: 'Upload' },
    ...(id
      ? [
          { path: `/videos/${id}/writing`, laptop: 'not designed (redirects to Workspace)', mobile: 'Writing script' },
          { path: `/videos/${id}/script`, laptop: 'Workspace', mobile: 'Script editor' },
          { path: `/videos/${id}/style`, laptop: 'part of Workspace (redirects)', mobile: 'Style' },
          { path: `/videos/${id}/rendering`, laptop: 'Rendering', mobile: 'Rendering' },
          { path: `/videos/${id}`, laptop: 'Player', mobile: 'Player' },
        ]
      : []),
  ]

  return (
    <div className="mx-auto flex max-w-[720px] flex-col gap-4 p-8">
      <h1 className="text-green font-serif text-[30px] font-bold">Screens</h1>
      <p className="text-muted text-[14px]">
        Laptop layout at 1180px and wider, mobile layout below that. Resize the window to switch.
        {!id && ' Make a video first to see the per-video screens.'}
      </p>
      <ul className="flex flex-col gap-3">
        {routes.map((route) => (
          <li key={route.path}>
            <Link to={route.path} className="bg-card rounded-card shadow-card flex flex-col gap-1 p-4">
              <span className="text-green text-[15px] font-semibold">{route.path}</span>
              <span className="text-muted text-[13px]">Laptop: {route.laptop}</span>
              <span className="text-muted text-[13px]">Mobile: {route.mobile}</span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}
