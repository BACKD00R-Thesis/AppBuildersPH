/** Small building blocks styled with the tokens in tailwind.config.js. */
import Ionicons from '@expo/vector-icons/Ionicons';
import type { ComponentProps, ReactNode } from 'react';
import { ActivityIndicator, Pressable, Text, View } from 'react-native';

import type { ProjectStatus, RenderStatus } from '@/lib/api';

export type IconName = ComponentProps<typeof Ionicons>['name'];

export const colors = {
  bg: '#0E0E12',
  surface: '#1A1A22',
  text: '#F5F5F7',
  textMuted: '#A0A0AE',
  primary: '#B6FF3B',
  onPrimary: '#0E0E12',
  danger: '#FF4D4D',
  success: '#3BFF8A',
};

type Variant = 'primary' | 'secondary' | 'ghost' | 'danger';

const variantClass: Record<Variant, { box: string; text: string; icon: string }> = {
  primary: { box: 'bg-primary', text: 'text-on-primary', icon: colors.onPrimary },
  secondary: { box: 'bg-surface-2 border border-border', text: 'text-text', icon: colors.text },
  ghost: { box: 'bg-transparent', text: 'text-text', icon: colors.text },
  danger: { box: 'bg-transparent border border-danger', text: 'text-danger', icon: colors.danger },
};

export function Button({
  title,
  onPress,
  variant = 'primary',
  icon,
  loading = false,
  disabled = false,
  className = '',
  accessibilityLabel,
}: {
  title: string;
  onPress: () => void;
  variant?: Variant;
  icon?: IconName;
  loading?: boolean;
  disabled?: boolean;
  className?: string;
  accessibilityLabel?: string;
}) {
  const style = variantClass[variant];
  const inactive = disabled || loading;
  return (
    <Pressable
      onPress={onPress}
      disabled={inactive}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel ?? title}
      accessibilityState={{ disabled: inactive, busy: loading }}
      className={`min-h-[48px] flex-row items-center justify-center gap-2 rounded-full px-5 active:opacity-80 ${style.box} ${inactive ? 'opacity-50' : ''} ${className}`}>
      {loading ? (
        <ActivityIndicator color={style.icon} />
      ) : (
        icon && <Ionicons name={icon} size={20} color={style.icon} />
      )}
      <Text className={`text-label ${style.text}`}>{title}</Text>
    </Pressable>
  );
}

export function IconButton({
  icon,
  onPress,
  label,
  color = colors.text,
  disabled = false,
}: {
  icon: IconName;
  onPress: () => void;
  label: string;
  color?: string;
  disabled?: boolean;
}) {
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      accessibilityRole="button"
      accessibilityLabel={label}
      hitSlop={6}
      className={`h-11 w-11 items-center justify-center rounded-full active:bg-surface-2 ${disabled ? 'opacity-30' : ''}`}>
      <Ionicons name={icon} size={22} color={color} />
    </Pressable>
  );
}

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <View className={`rounded-md border border-border bg-surface p-4 ${className}`}>{children}</View>;
}

export function ErrorBanner({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <View
      accessibilityRole="alert"
      className="flex-row items-start gap-3 rounded-md border border-danger/40 bg-danger/10 p-3">
      <Ionicons name="alert-circle" size={20} color={colors.danger} />
      <Text className="flex-1 text-body text-text">{message}</Text>
      {onRetry && (
        <Pressable onPress={onRetry} accessibilityRole="button" hitSlop={8}>
          <Text className="text-label text-primary">Retry</Text>
        </Pressable>
      )}
    </View>
  );
}

export function EmptyState({
  icon,
  title,
  action,
}: {
  icon: IconName;
  title: string;
  action?: ReactNode;
}) {
  return (
    <View className="items-center gap-4 px-6 py-16">
      <View className="h-20 w-20 items-center justify-center rounded-full bg-surface">
        <Ionicons name={icon} size={36} color={colors.primary} />
      </View>
      <Text className="text-center text-body text-text-muted">{title}</Text>
      {action}
    </View>
  );
}

const statusStyle: Record<ProjectStatus | RenderStatus, { label: string; className: string }> = {
  ready: { label: 'No script', className: 'bg-surface-2 text-text-muted' },
  generating: { label: 'Writing…', className: 'bg-accent/20 text-accent' },
  scripted: { label: 'Script ready', className: 'bg-speaker-a/20 text-speaker-a' },
  failed: { label: 'Failed', className: 'bg-danger/20 text-danger' },
  queued: { label: 'Queued', className: 'bg-surface-2 text-text-muted' },
  running: { label: 'Rendering…', className: 'bg-accent/20 text-accent' },
  done: { label: 'Video ready', className: 'bg-success/20 text-success' },
  canceled: { label: 'Canceled', className: 'bg-surface-2 text-text-muted' },
};

export function StatusPill({ status }: { status: ProjectStatus | RenderStatus }) {
  const style = statusStyle[status];
  return (
    <Text className={`self-start overflow-hidden rounded-full px-3 py-1 text-caption ${style.className}`}>
      {style.label}
    </Text>
  );
}

export function SectionTitle({ children }: { children: ReactNode }) {
  return <Text className="text-title text-text">{children}</Text>;
}
