import Ionicons from '@expo/vector-icons/Ionicons';
import { Text, View } from 'react-native';

import { colors } from '@/components/ui';
import type { Render } from '@/lib/api';

/** Render steps reported by the server (app/workflow.py), in order. */
const STEPS = [
  { key: 'voices', label: 'Recording voices' },
  { key: 'captions', label: 'Timing captions' },
  { key: 'mixing', label: 'Mixing audio' },
  { key: 'rendering', label: 'Rendering video' },
] as const;

export function ProgressSteps({ render }: { render: Render }) {
  const done = render.status === 'done';
  const currentIndex = done ? STEPS.length : STEPS.findIndex((s) => s.key === render.step);
  const percent = Math.round(render.progress * 100);

  return (
    <View className="gap-4">
      <View
        className="h-3 overflow-hidden rounded-full bg-surface-2"
        accessibilityRole="progressbar"
        accessibilityValue={{ min: 0, max: 100, now: percent }}>
        <View className="h-full rounded-full bg-primary" style={{ width: `${percent}%` }} />
      </View>
      <Text className="text-label text-text-muted">
        {render.status === 'queued' ? 'Waiting for the server…' : `${percent}%`}
      </Text>
      <View className="gap-3">
        {STEPS.map((step, i) => {
          const state = i < currentIndex ? 'done' : i === currentIndex ? 'active' : 'todo';
          return (
            <View key={step.key} className="flex-row items-center gap-3">
              <Ionicons
                name={state === 'done' ? 'checkmark-circle' : state === 'active' ? 'radio-button-on' : 'ellipse-outline'}
                size={22}
                color={state === 'todo' ? colors.textMuted : state === 'done' ? colors.success : colors.primary}
              />
              <Text className={`text-body ${state === 'todo' ? 'text-text-muted' : 'text-text'}`}>{step.label}</Text>
            </View>
          );
        })}
      </View>
    </View>
  );
}
