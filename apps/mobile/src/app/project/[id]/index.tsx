import { useAudioPlayer, useAudioPlayerStatus } from 'expo-audio';
import { router, Stack, useLocalSearchParams } from 'expo-router';
import { useEffect, useRef, useState } from 'react';
import { ActivityIndicator, Alert, KeyboardAvoidingView, Platform, ScrollView, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { type DraftLine, LineCard } from '@/components/line-card';
import { Button, colors, EmptyState, ErrorBanner, IconButton, StatusPill } from '@/components/ui';
import type { Character, Line, Project } from '@/lib/api';
import { usePollWhile, useResource } from '@/lib/hooks';
import { useServer } from '@/lib/server';

let keyCounter = 0;
const nextKey = () => `new-${++keyCounter}`;

function toDrafts(lines: Line[]): DraftLine[] {
  return lines.map((l) => ({ key: l.id, id: l.id, character_id: l.character_id, text: l.text }));
}

function sameScript(drafts: DraftLine[], lines: Line[]): boolean {
  return (
    drafts.length === lines.length &&
    drafts.every((d, i) => d.id === lines[i].id && d.text.trim() === lines[i].text && d.character_id === lines[i].character_id)
  );
}

export default function ScriptScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { api } = useServer();
  const [drafts, setDrafts] = useState<DraftLine[]>([]);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [saving, setSaving] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [previewKey, setPreviewKey] = useState<string | null>(null);
  const [loadingPreviewKey, setLoadingPreviewKey] = useState<string | null>(null);
  const loadedVersion = useRef<string | null>(null);

  const player = useAudioPlayer(null);
  const playerStatus = useAudioPlayerStatus(player);

  const project = useResource(() => api.getProject(id));
  const data = project.data;
  // Covers both arriving mid-generation and starting a rewrite from this screen.
  usePollWhile(data?.status === 'generating', project.reload);

  useEffect(() => {
    api.characters().then(setCharacters, () => setCharacters([]));
  }, [api]);

  // Load the server's script into the editor whenever it changes (first load, generation finished).
  useEffect(() => {
    if (!data || data.status === 'generating') return;
    const version = data.lines.map((l) => `${l.id}:${l.character_id}:${l.text}`).join('|');
    if (version !== loadedVersion.current) {
      loadedVersion.current = version;
      setDrafts(toDrafts(data.lines));
    }
  }, [data]);

  const dirty = !!data && !sameScript(drafts, data.lines);
  const generating = data?.status === 'generating';

  async function save(): Promise<Project | null> {
    if (!data) return null;
    const lines = drafts.filter((d) => d.text.trim());
    if (lines.length === 0) {
      setActionError('Add at least one line first.');
      return null;
    }
    setSaving(true);
    setActionError(null);
    try {
      const saved = await api.saveScript(
        data.id,
        lines.map((d) => ({ id: d.id, character_id: d.character_id, text: d.text.trim() })),
      );
      loadedVersion.current = null;
      project.setData(saved);
      return saved;
    } catch (err) {
      setActionError(err instanceof Error ? err.message : String(err));
      return null;
    } finally {
      setSaving(false);
    }
  }

  async function preview(index: number) {
    const draft = drafts[index];
    if (previewKey === draft.key && playerStatus.playing) {
      player.pause();
      setPreviewKey(null);
      return;
    }
    if (!draft.text.trim()) {
      setActionError('Write something on this line first.');
      return;
    }
    setLoadingPreviewKey(draft.key);
    setActionError(null);
    try {
      // Previews play what's on the server, so save edits first.
      let lineId = draft.id;
      if (dirty || !lineId) {
        const saved = await save();
        if (!saved) return;
        lineId = saved.lines[drafts.slice(0, index).filter((d) => d.text.trim()).length]?.id;
      }
      if (!lineId) return;
      const { audio_url } = await api.previewLine(lineId);
      player.replace({ uri: api.mediaUrl(audio_url), headers: api.headers });
      player.seekTo(0);
      player.play();
      setPreviewKey(lineId);
    } catch (err) {
      setActionError(err instanceof Error ? err.message : String(err));
    } finally {
      setLoadingPreviewKey(null);
    }
  }

  async function regenerate() {
    const run = async () => {
      setActionError(null);
      try {
        project.setData(await api.generateScript(id));
      } catch (err) {
        setActionError(err instanceof Error ? err.message : String(err));
      }
    };
    if (drafts.length === 0) return run();
    Alert.alert('Rewrite the script?', 'This replaces every line, including your edits.', [
      { text: 'Cancel', style: 'cancel' },
      { text: 'Rewrite', style: 'destructive', onPress: run },
    ]);
  }

  async function next() {
    if (dirty && !(await save())) return;
    router.push({ pathname: '/project/[id]/style', params: { id } });
  }

  function update(index: number, patch: Partial<DraftLine>) {
    setDrafts((list) => list.map((d, i) => (i === index ? { ...d, ...patch } : d)));
  }

  function toggleSpeaker(index: number) {
    if (characters.length < 2) return;
    const current = characters.findIndex((c) => c.id === drafts[index].character_id);
    update(index, { character_id: characters[(current + 1) % characters.length].id });
  }

  function move(index: number, delta: -1 | 1) {
    setDrafts((list) => {
      const target = index + delta;
      if (target < 0 || target >= list.length) return list;
      const copy = [...list];
      [copy[index], copy[target]] = [copy[target], copy[index]];
      return copy;
    });
  }

  function addLine() {
    const last = drafts[drafts.length - 1];
    const other = characters.find((c) => c.id !== last?.character_id) ?? characters[0];
    if (!other) return;
    setDrafts((list) => [...list, { key: nextKey(), character_id: other.id, text: '' }]);
  }

  if (!data) {
    return (
      <View className="flex-1 items-center justify-center gap-4 bg-bg p-6">
        {project.error ? (
          <ErrorBanner message={project.error.message} onRetry={project.reload} />
        ) : (
          <ActivityIndicator color={colors.primary} />
        )}
      </View>
    );
  }

  return (
    <SafeAreaView edges={['bottom']} className="flex-1 bg-bg">
      <Stack.Screen
        options={{
          title: data.title,
          headerRight: () => (
            <IconButton
              icon="refresh"
              label="Rewrite the script with AI"
              disabled={generating}
              onPress={regenerate}
            />
          ),
        }}
      />
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} className="flex-1">
        <ScrollView contentContainerClassName="gap-3 p-4 pb-8" keyboardShouldPersistTaps="handled">
          <View className="flex-row items-center gap-2">
            <StatusPill status={data.status} />
            <Text className="text-caption text-text-muted">
              {data.page_count} {data.page_count === 1 ? 'page' : 'pages'}
              {data.pages ? ` (using ${data.pages})` : ''} · {data.text_chars.toLocaleString()} characters
            </Text>
          </View>

          {(actionError || data.error) && <ErrorBanner message={actionError ?? data.error ?? ''} />}

          {generating ? (
            <View className="items-center gap-4 py-16">
              <ActivityIndicator size="large" color={colors.primary} />
              <Text className="text-center text-body text-text">Writing the dialogue…</Text>
              <Text className="text-center text-caption text-text-muted">
                The local AI is reading your PDF. This takes 20 to 90 seconds.
              </Text>
            </View>
          ) : drafts.length === 0 ? (
            <EmptyState
              icon="chatbubbles-outline"
              title="No script yet."
              action={<Button title="Write the script" icon="sparkles" onPress={regenerate} />}
            />
          ) : (
            <>
              <Text className="text-caption text-text-muted">
                AI scripts can get facts wrong. Check each line before you share the video.
              </Text>
              {drafts.map((draft, index) => (
                <LineCard
                  key={draft.key}
                  line={draft}
                  index={index}
                  total={drafts.length}
                  characters={characters}
                  dirty={dirty}
                  playing={previewKey !== null && previewKey === draft.id && playerStatus.playing}
                  loadingPreview={loadingPreviewKey === draft.key}
                  onChangeText={(text) => update(index, { text })}
                  onToggleSpeaker={() => toggleSpeaker(index)}
                  onMove={(delta) => move(index, delta)}
                  onDelete={() => setDrafts((list) => list.filter((_, i) => i !== index))}
                  onPreview={() => preview(index)}
                />
              ))}
              <Button title="Add line" icon="add" variant="secondary" onPress={addLine} />
            </>
          )}
        </ScrollView>

        {!generating && drafts.length > 0 && (
          <View className="flex-row gap-3 border-t border-border px-4 pb-4 pt-3">
            {dirty && <Button title="Save" variant="secondary" onPress={save} loading={saving} className="flex-1" />}
            <Button
              title="Next: style"
              icon="arrow-forward"
              onPress={next}
              disabled={saving}
              className="flex-1"
            />
          </View>
        )}
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
