import Ionicons from '@expo/vector-icons/Ionicons';
import { router, Stack } from 'expo-router';
import { useState } from 'react';
import { FlatList, Pressable, RefreshControl, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button, colors, EmptyState, ErrorBanner, IconButton, StatusPill } from '@/components/ui';
import type { ProjectSummary } from '@/lib/api';
import { useResource } from '@/lib/hooks';
import { librarySupported, listSaved, type SavedVideo } from '@/lib/library';
import { useServer } from '@/lib/server';

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
}

function SavedRow({ videos }: { videos: SavedVideo[] }) {
  if (videos.length === 0) return null;
  return (
    <View className="gap-3 pb-6">
      <Text className="text-label text-text-muted">ON THIS PHONE</Text>
      {videos.map((video) => (
        <Pressable
          key={video.renderId}
          onPress={() => router.push({ pathname: '/watch', params: { uri: video.uri, title: video.title } })}
          accessibilityRole="button"
          accessibilityLabel={`Play ${video.title}`}
          className="flex-row items-center gap-3 rounded-md bg-surface p-3 active:bg-surface-2">
          <View className="h-12 w-12 items-center justify-center rounded-sm bg-primary/15">
            <Ionicons name="play" size={22} color={colors.primary} />
          </View>
          <View className="flex-1">
            <Text className="text-body text-text" numberOfLines={1}>
              {video.title}
            </Text>
            <Text className="text-caption text-text-muted">
              {video.durationS ? `${Math.round(video.durationS)}s · ` : ''}
              {formatDate(video.savedAt)}
            </Text>
          </View>
        </Pressable>
      ))}
    </View>
  );
}

function ProjectRow({ project }: { project: ProjectSummary }) {
  const render = project.latest_render;
  return (
    <Pressable
      onPress={() => router.push({ pathname: '/project/[id]', params: { id: project.id } })}
      accessibilityRole="button"
      accessibilityLabel={`Open ${project.title}`}
      className="gap-2 rounded-md border border-border bg-surface p-4 active:bg-surface-2">
      <Text className="text-body font-semibold text-text" numberOfLines={2}>
        {project.title}
      </Text>
      <View className="flex-row items-center gap-2">
        <StatusPill status={render ? render.status : project.status} />
        <Text className="text-caption text-text-muted">
          {project.page_count} {project.page_count === 1 ? 'page' : 'pages'} · {formatDate(project.created_at)}
        </Text>
      </View>
    </Pressable>
  );
}

export default function LibraryScreen() {
  const { api, config } = useServer();
  const [saved, setSaved] = useState<SavedVideo[]>([]);
  const projects = useResource(
    async () => {
      if (librarySupported) setSaved(listSaved());
      return api.listProjects();
    },
    { shouldPoll: (list) => list.some((p) => p.status === 'generating' || p.latest_render?.status === 'running') },
  );

  const noServer = !config.apiUrl;

  return (
    <SafeAreaView edges={['bottom']} className="flex-1 bg-bg">
      <Stack.Screen
        options={{
          headerRight: () => (
            <IconButton icon="settings-outline" label="Server settings" onPress={() => router.push('/settings')} />
          ),
        }}
      />
      <FlatList
        data={projects.data ?? []}
        keyExtractor={(p) => p.id}
        contentContainerClassName="gap-3 px-4 pb-32 pt-2"
        refreshControl={
          <RefreshControl refreshing={false} onRefresh={projects.reload} tintColor={colors.primary} />
        }
        ListHeaderComponent={
          <View className="gap-4 pb-3">
            <Text className="text-body text-text-muted">
              Turn study PDFs into short videos where two characters explain the material.
            </Text>
            {noServer ? (
              <ErrorBanner message="Connect to the AI server on your computer to get started." />
            ) : (
              projects.error && <ErrorBanner message={projects.error.message} onRetry={projects.reload} />
            )}
            <SavedRow videos={saved} />
            {(projects.data?.length ?? 0) > 0 && <Text className="text-label text-text-muted">PROJECTS</Text>}
          </View>
        }
        renderItem={({ item }) => <ProjectRow project={item} />}
        ListEmptyComponent={
          projects.loading || projects.error || noServer ? null : (
            <EmptyState icon="document-text-outline" title="No videos yet. Upload a lecture PDF to make your first one." />
          )
        }
      />
      <View className="absolute bottom-0 left-0 right-0 px-4 pb-8">
        {noServer ? (
          <Button title="Connect to server" icon="wifi" onPress={() => router.push('/settings')} />
        ) : (
          <Button title="New video from PDF" icon="add" onPress={() => router.push('/new')} />
        )}
      </View>
    </SafeAreaView>
  );
}
