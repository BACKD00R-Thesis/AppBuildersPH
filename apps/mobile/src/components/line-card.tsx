import { ActivityIndicator, Pressable, Text, TextInput, View } from 'react-native';

import { colors, IconButton } from '@/components/ui';
import type { Character } from '@/lib/api';

export interface DraftLine {
  key: string;
  id?: string;
  character_id: string;
  text: string;
}

export function LineCard({
  line,
  index,
  total,
  characters,
  playing,
  loadingPreview,
  dirty,
  onChangeText,
  onToggleSpeaker,
  onMove,
  onDelete,
  onPreview,
}: {
  line: DraftLine;
  index: number;
  total: number;
  characters: Character[];
  playing: boolean;
  loadingPreview: boolean;
  /** Unsaved changes: previews play the saved version, so saving comes first. */
  dirty: boolean;
  onChangeText: (text: string) => void;
  onToggleSpeaker: () => void;
  onMove: (delta: -1 | 1) => void;
  onDelete: () => void;
  onPreview: () => void;
}) {
  const character = characters.find((c) => c.id === line.character_id);
  const color = character?.color ?? colors.text;
  return (
    <View className="gap-2 rounded-md border border-border bg-surface p-3" style={{ borderLeftColor: color, borderLeftWidth: 4 }}>
      <View className="flex-row items-center">
        <Pressable
          onPress={onToggleSpeaker}
          accessibilityRole="button"
          accessibilityLabel={`Speaker: ${character?.name ?? line.character_id}. Tap to switch.`}
          hitSlop={8}
          className="flex-row items-center gap-2 rounded-full bg-surface-2 px-3 py-1">
          <View className="h-3 w-3 rounded-full" style={{ backgroundColor: color }} />
          <Text className="text-label" style={{ color }}>
            {character?.name ?? line.character_id}
          </Text>
        </Pressable>
        <View className="flex-1" />
        {loadingPreview ? (
          <View className="h-11 w-11 items-center justify-center">
            <ActivityIndicator color={colors.primary} />
          </View>
        ) : (
          <IconButton
            icon={playing ? 'stop-circle' : 'play-circle'}
            label={playing ? 'Stop preview' : dirty ? 'Save and preview this line' : 'Preview this line'}
            color={playing ? colors.primary : colors.text}
            onPress={onPreview}
          />
        )}
        <IconButton icon="arrow-up" label="Move line up" disabled={index === 0} onPress={() => onMove(-1)} />
        <IconButton
          icon="arrow-down"
          label="Move line down"
          disabled={index === total - 1}
          onPress={() => onMove(1)}
        />
        <IconButton icon="trash-outline" label="Delete line" color={colors.danger} onPress={onDelete} />
      </View>
      <TextInput
        value={line.text}
        onChangeText={onChangeText}
        multiline
        maxLength={400}
        placeholder="What do they say?"
        placeholderTextColor={colors.textMuted}
        accessibilityLabel={`Line ${index + 1} text`}
        className="min-h-[48px] rounded-sm bg-surface-2 px-3 py-2 text-body text-text"
        textAlignVertical="top"
      />
    </View>
  );
}
