import Ionicons from '@expo/vector-icons/Ionicons';
import { Image } from 'expo-image';
import { router, useLocalSearchParams } from 'expo-router';
import { useState } from 'react';
import { ActivityIndicator, Pressable, ScrollView, Text, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button, colors, ErrorBanner, SectionTitle } from '@/components/ui';
import type { Background, Character } from '@/lib/api';
import { useResource } from '@/lib/hooks';
import { useServer } from '@/lib/server';

function BackgroundOption({
  background,
  selected,
  onSelect,
}: {
  background: Background;
  selected: boolean;
  onSelect: () => void;
}) {
  return (
    <Pressable
      onPress={onSelect}
      accessibilityRole="radio"
      accessibilityState={{ selected }}
      accessibilityLabel={background.name}
      className={`w-[47%] gap-2 rounded-md border-2 bg-surface p-3 ${selected ? 'border-primary' : 'border-border'}`}>
      <View className="aspect-[9/16] w-full items-center justify-center rounded-sm bg-surface-2">
        <Ionicons
          name={background.builtin ? 'grid-outline' : 'game-controller-outline'}
          size={32}
          color={selected ? colors.primary : colors.textMuted}
        />
      </View>
      <View className="flex-row items-center gap-2">
        <Text className="flex-1 text-label text-text" numberOfLines={1}>
          {background.name}
        </Text>
        {selected && <Ionicons name="checkmark-circle" size={20} color={colors.primary} />}
      </View>
      {background.builtin && <Text className="text-caption text-text-muted">Built in</Text>}
    </Pressable>
  );
}

function CharacterChip({ character, imageUrl, headers }: { character: Character; imageUrl: string; headers: Record<string, string> }) {
  return (
    <View className="flex-1 items-center gap-2 rounded-md bg-surface p-3">
      {character.has_image ? (
        <Image source={{ uri: imageUrl, headers }} style={{ width: 72, height: 72 }} contentFit="contain" />
      ) : (
        <View className="h-[72px] w-[72px] items-center justify-center rounded-full" style={{ backgroundColor: character.color }}>
          <Text className="text-title text-on-primary">{character.name[0]}</Text>
        </View>
      )}
      <Text className="text-label" style={{ color: character.color }}>
        {character.name}
      </Text>
      <Text className="text-center text-caption text-text-muted">{character.role === 'asker' ? 'Asks' : 'Explains'}</Text>
    </View>
  );
}

export default function StyleScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { api } = useServer();
  const [selected, setSelected] = useState<string | null>(null);
  const [starting, setStarting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const assets = useResource(async () => {
    const [backgrounds, characters] = await Promise.all([api.backgrounds(), api.characters()]);
    return { backgrounds, characters };
  });
  const backgroundId = selected ?? assets.data?.backgrounds[0]?.id ?? null;

  async function render() {
    setStarting(true);
    setError(null);
    try {
      const job = await api.startRender(id, backgroundId);
      router.replace({ pathname: '/render/[id]', params: { id: job.id } });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setStarting(false);
    }
  }

  return (
    <SafeAreaView edges={['bottom']} className="flex-1 bg-bg">
      <ScrollView contentContainerClassName="gap-6 p-4 pb-8">
        {assets.error && <ErrorBanner message={assets.error.message} onRetry={assets.reload} />}
        {!assets.data ? (
          !assets.error && <ActivityIndicator color={colors.primary} className="py-16" />
        ) : (
          <>
            <View className="gap-3">
              <SectionTitle>Cast</SectionTitle>
              <View className="flex-row gap-3">
                {assets.data.characters.map((c) => (
                  <CharacterChip key={c.id} character={c} imageUrl={api.characterImageUrl(c.id)} headers={api.headers} />
                ))}
              </View>
            </View>

            <View className="gap-3" accessibilityRole="radiogroup">
              <SectionTitle>Background</SectionTitle>
              <View className="flex-row flex-wrap justify-between gap-y-3">
                {assets.data.backgrounds.map((bg) => (
                  <BackgroundOption
                    key={bg.id}
                    background={bg}
                    selected={bg.id === backgroundId}
                    onSelect={() => setSelected(bg.id)}
                  />
                ))}
              </View>
              <Text className="text-caption text-text-muted">
                Add your own gameplay clips on the server in assets/backgrounds (see docs/development.md).
              </Text>
            </View>
          </>
        )}
        {error && <ErrorBanner message={error} />}
      </ScrollView>
      <View className="px-4 pb-4">
        <Button title="Render video" icon="film-outline" onPress={render} loading={starting} disabled={!assets.data} />
      </View>
    </SafeAreaView>
  );
}
