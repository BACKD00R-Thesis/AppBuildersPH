import { useEffect } from 'react'
import { Navigate, useNavigate, useParams } from 'react-router-dom'
import { Button } from '../../components/Button'
import { Icon } from '../../components/Icon'
import { Notice, NoticeAction } from '../../components/Notice'
import { ScriptSteps, scriptHeadline, useSecondsLeft } from '../../components/ScriptProgress'
import { MobileBottomBar, MobileShell, MobileTitleRow } from '../../layouts/MobileShell'
import { useProject } from '../../lib/useProject'

/** Figma: Mobile v2 / Writing script (14:146). Opens the script when the engine finishes. */
export function WritingScript() {
  const { id } = useParams()
  const navigate = useNavigate()
  const { project, notFound, regenerate, error } = useProject(id)
  const secondsLeft = useSecondsLeft(project)

  const scripted = project?.status === 'scripted'
  useEffect(() => {
    if (scripted) navigate(`/videos/${id}/script`, { replace: true })
  }, [scripted, id, navigate])

  if (notFound) return <Navigate to="/" replace />

  const failed = project?.status === 'failed'
  const notStarted = project?.status === 'ready'

  return (
    <MobileShell
      headerClassName="gap-[14px] pb-[26px]"
      bodyClassName="gap-4"
      header={
        <>
          <MobileTitleRow backTo="/" title="Writing script" />
          <p className="text-page w-full font-serif text-[28px] leading-[34px] font-bold">
            {!project ? '' : failed ? 'The script didn’t come out' : scriptHeadline(project)}
          </p>
          <p className="text-on-green text-[14px] whitespace-nowrap">{failed || notStarted ? project?.title : secondsLeft}</p>
        </>
      }
      footer={
        <MobileBottomBar>
          {failed || notStarted ? (
            <Button className="w-full" onClick={regenerate}>
              {failed ? 'Try again' : 'Write the script'}
            </Button>
          ) : (
            <Button variant="ghost" to="/" className="w-full">
              Back to home
            </Button>
          )}
        </MobileBottomBar>
      }
    >
      {error && <Notice>{error}</Notice>}
      {failed && (
        <Notice action={<NoticeAction onClick={regenerate}>Retry</NoticeAction>}>
          {project?.error ?? 'Something went wrong while writing.'}
        </Notice>
      )}

      {project && !failed && (
        <div className="w-full shrink-0">
          <ScriptSteps project={project} density="mobile" />
        </div>
      )}

      <p className="eyebrow text-green-2 shrink-0">Preview</p>

      {/* Skeleton script lines, alternating Tito Boy (mint) and Bunso (card). */}
      <div aria-hidden className="bg-mint rounded-card flex w-full shrink-0 flex-col gap-[10px] p-4">
        <Icon name="skeletonHeadLight" className="self-start" />
        <div className="bg-card h-[10px] w-[180px] rounded-[6px]" />
        <div className="bg-card h-[10px] w-[120px] rounded-[6px]" />
      </div>
      <div aria-hidden className="bg-card rounded-card flex w-full shrink-0 flex-col gap-[10px] p-4">
        <Icon name="skeletonHeadMint" className="self-start" />
        <div className="bg-mint h-[10px] w-[220px] rounded-[6px]" />
        <div className="bg-mint h-[10px] w-[160px] rounded-[6px]" />
      </div>
      <div aria-hidden className="bg-mint rounded-card flex w-full shrink-0 flex-col gap-[10px] p-4">
        <Icon name="skeletonHeadLight" className="self-start" />
        <div className="bg-card h-[10px] w-[140px] rounded-[6px]" />
      </div>
    </MobileShell>
  )
}
