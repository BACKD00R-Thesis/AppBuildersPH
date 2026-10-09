import Ionicons from '@expo/vector-icons/Ionicons';
import * as DocumentPicker from 'expo-document-picker';
import { router } from 'expo-router';
import { useState } from 'react';
import { KeyboardAvoidingView, Platform, Pressable, ScrollView, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { Button, colors, ErrorBanner } from '@/components/ui';
import type { PickedFile } from '@/lib/api';
import { useServer } from '@/lib/server';

const MAX_MB = 20;

export default function NewProjectScreen() {
  const { api } = useServer();
  const [file, setFile] = useState<(PickedFile & { size?: number }) | null>(null);
  const [title, setTitle] = useState('');
  const [pages, setPages] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [step, setStep] = useState<'idle' | 'uploading' | 'starting'>('idle');

  async function pick() {
    setError(null);
    const result = await DocumentPicker.getDocumentAsync({
      type: 'application/pdf',
      copyToCacheDirectory: true,
    });
    if (result.canceled) return;
    const asset = result.assets[0];
    if (asset.size && asset.size > MAX_MB * 1024 * 1024) {
      setError(`That PDF is over ${MAX_MB} MB. Try a smaller file or split it.`);
      return;
    }
    setFile({ uri: asset.uri, name: asset.name, mimeType: asset.mimeType, file: asset.file, size: asset.size });
    if (!title) setTitle(asset.name.replace(/\.pdf$/i, ''));
  }

  async function create() {
    if (!file) return;
    setError(null);
    try {
      setStep('uploading');
      const project = await api.uploadProject(file, { title: title.trim(), pages: pages.trim() });
      setStep('starting');
      await api.generateScript(project.id);
      router.replace({ pathname: '/project/[id]', params: { id: project.id } });
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      setStep('idle');
    }
  }

  const busy = step !== 'idle';

  return (
    <SafeAreaView edges={['bottom']} className="flex-1 bg-bg">
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} className="flex-1">
        <ScrollView contentContainerClassName="gap-5 p-4 pb-12" keyboardShouldPersistTaps="handled">
          <Pressable
            onPress={pick}
            disabled={busy}
            accessibilityRole="button"
            accessibilityLabel={file ? `Selected ${file.name}. Tap to choose another PDF.` : 'Choose a PDF'}
            className="items-center gap-3 rounded-lg border-2 border-dashed border-border bg-surface px-6 py-10 active:bg-surface-2">
            <Ionicons name={file ? 'document-text' : 'cloud-upload-outline'} size={44} color={colors.primary} />
            <Text className="text-center text-body font-semibold text-text" numberOfLines={2}>
              {file ? file.name : 'Choose a lecture PDF'}
            </Text>
            <Text className="text-center text-caption text-text-muted">
              {file
                ? `${file.size ? `${(file.size / 1024 / 1024).toFixed(1)} MB · ` : ''}Tap to change`
                : `Slides, papers or textbook chapters. Up to 50 pages, ${MAX_MB} MB.`}
            </Text>
          </Pressable>

          <View className="gap-2">
            <Text className="text-label text-text">Title</Text>
            <TextInput
              value={title}
              onChangeText={setTitle}
              placeholder="e.g. Photosynthesis"
              placeholderTextColor={colors.textMuted}
              maxLength={120}
              accessibilityLabel="Title"
              className="min-h-[48px] rounded-sm border border-border bg-surface px-3 text-body text-text"
            />
          </View>

          <View className="gap-2">
            <Text className="text-label text-text">Pages (optional)</Text>
            <TextInput
              value={pages}
              onChangeText={setPages}
              placeholder="All pages, or e.g. 3-7, 10"
              placeholderTextColor={colors.textMuted}
              keyboardType={Platform.OS === 'ios' ? 'numbers-and-punctuation' : 'default'}
              accessibilityLabel="Pages"
              className="min-h-[48px] rounded-sm border border-border bg-surface px-3 text-body text-text"
            />
            <Text className="text-caption text-text-muted">
              Shorter selections make better videos. One topic per video works best.
            </Text>
          </View>

          {error && <ErrorBanner message={error} />}
        </ScrollView>
        <View className="px-4 pb-4">
          <Button
            title={step === 'uploading' ? 'Reading PDF…' : step === 'starting' ? 'Starting…' : 'Write the script'}
            icon="sparkles"
            onPress={create}
            loading={busy}
            disabled={!file}
          />
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}
