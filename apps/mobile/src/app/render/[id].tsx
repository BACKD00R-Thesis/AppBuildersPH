import { router, Stack, useLocalSearchParams } from 'expo-router';
import * as Sharing from 'expo-sharing';
import { useVideoPlayer, VideoView } from 'expo-video';
import { useState } from 'react';
import { ActivityIndicator, ScrollView, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { ProgressSteps } from '@/components/progress-steps';
import { Button, colors, ErrorBanner } from '@/components/ui';
import type { Api, Render } from '@/lib/api';
import { usePollWhile, useResource } from '@/lib/hooks';
import { findSaved, librarySupported, saveRender, type SavedVideo } from '@/lib/library';
import { useServer } from '@/lib/server';

const ACTIVE = new Set(['queued', 'running']);

function Player({ api, render }: { api: Api; render: Render }) {
  const player = useVideoPlayer(
    { uri: api.mediaUrl(render.video_url ?? ''), headers: api.headers },
    (p) => {
      p.loop = true;
      p.play();
    },
  );
  return (
    <View className="aspect-[9/16] w-full max-w-[360px] self-center overflow-hidden rounded-md bg-black">
      <VideoView player={player} style={{ flex: 1 }} contentFit="contain" nativeControls fullscreenOptions={{ enable: true }} />
    </View>
  );
}

export default function RenderScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { api } = useServer();
  const [saved, setSaved] = useState<SavedVideo | undefined>(() => (librarySupported ? findSaved(id) : undefined));
  const [downloading, setDownloading] = useState<number | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const job = useResource(async () => {
    const render = await api.getRender(id);
    const project = await api.getProject(render.project_id);
    return { render, title: project.title };
  });
  const render = job.data?.render;
  usePollWhile(!!render && ACTIVE.has(render.status), job.reload, 1000);

  async function save(): Promise<SavedVideo | undefined> {
    if (!render || !job.data) return;
    if (saved) return saved;
    setActionError(null);
    setDownloading(0);
    try {
      const video = await saveRender(api, render, job.data.title, setDownloading);
      setSaved(video);
      return video;
    } catch (err) {
      setActionError(err instanceof Error ? err.message : String(err));
    } finally {
      setDownloading(null);
    }
  }

  async function share() {
    const video = await save();
    if (video && (await Sharing.isAvailableAsync())) {
      await Sharing.shareAsync(video.uri, { mimeType: 'video/mp4', dialogTitle: job.data?.title });
    }
  }

  async function cancel() {
    setBusy(true);
    try {
      job.setData((current) => current && { ...current, render: { ...current.render, status: 'canceled' } });
      await api.cancelRender(id);
      await job.reload();
    } catch (err) {
      setActionError(err instanceof Error ? err.message : String(err));
    } finally {
      setBusy(false);
    }
  }

  async function retry() {
    if (!render) return;
    setBusy(true);
    setActionError(null);
    try {
      const next = await api.startRender(render.project_id, render.background_id);
      router.replace({ pathname: '/render/[id]', params: { id: next.id } });
    } catch (err) {
      setActionError(err instanceof Error ? err.message : String(err));
      setBusy(false);
    }
  }

  if (!render) {
    return (
      <View className="flex-1 items-center justify-center bg-bg p-6">
        {job.error ? <ErrorBanner message={job.error.message} onRetry={job.reload} /> : <ActivityIndicator color={colors.primary} />}
      </View>
    );
  }

  const editScript = () => router.dismissTo({ pathname: '/project/[id]', params: { id: render.project_id } });

  return (
    <SafeAreaView edges={['bottom']} className="flex-1 bg-bg">
      <Stack.Screen options={{ title: job.data?.title ?? 'Render' }} />
      <ScrollView contentContainerClassName="gap-6 p-4 pb-10">
        {ACTIVE.has(render.status) && (
          <>
            <Text className="text-title text-text">Making your video</Text>
            <ProgressSteps render={render} />
            <Text className="text-caption text-text-muted">
              Everything runs on your computer. You can leave this screen; the render keeps going.
            </Text>
            <Button title="Cancel render" variant="danger" onPress={cancel} loading={busy} />
          </>
        )}

        {render.status === 'done' && (
          <>
            <Player api={api} render={render} />
            <View className="gap-3">
              {librarySupported && (
                <Button
                  title={saved ? 'Saved on this phone' : downloading !== null ? `Saving… ${Math.round(downloading * 100)}%` : 'Save to phone'}
                  icon={saved ? 'checkmark-circle' : 'download-outline'}
                  onPress={save}
                  disabled={!!saved}
                  loading={downloading !== null}
                />
              )}
              {librarySupported && <Button title="Share" icon="share-outline" variant="secondary" onPress={share} />}
              <Button title="Edit script" icon="create-outline" variant="ghost" onPress={editScript} />
            </View>
          </>
        )}

        {(render.status === 'failed' || render.status === 'canceled') && (
          <View className="gap-4">
            <Text className="text-title text-text">{render.status === 'failed' ? 'Render failed' : 'Render canceled'}</Text>
            {render.error && <ErrorBanner message={render.error} />}
            <Button title="Try again" icon="refresh" onPress={retry} loading={busy} />
            <Button title="Edit script" icon="create-outline" variant="ghost" onPress={editScript} />
          </View>
        )}

        {actionError && <ErrorBanner message={actionError} />}
      </ScrollView>
    </SafeAreaView>
  );
}
