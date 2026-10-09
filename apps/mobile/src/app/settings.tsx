import Ionicons from '@expo/vector-icons/Ionicons';
import { router } from 'expo-router';
import { useState } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, Text, TextInput, View } from 'react-native';

import { Button, Card, colors, ErrorBanner } from '@/components/ui';
import { createApi, type Health, normalizeUrl } from '@/lib/api';
import { useServer } from '@/lib/server';

const ENGINE_LABELS: Record<keyof Health['engines'], string> = {
  llm: 'Script writer (Ollama)',
  tts: 'Voices (TTS)',
  alignment: 'Caption timing',
  ffmpeg: 'Video renderer (FFmpeg)',
};

export default function SettingsScreen() {
  const { config, setConfig } = useServer();
  const [apiUrl, setApiUrl] = useState(config.apiUrl);
  const [token, setToken] = useState(config.token);
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [testing, setTesting] = useState(false);

  async function test(): Promise<boolean> {
    setTesting(true);
    setError(null);
    setHealth(null);
    try {
      const result = await createApi({ apiUrl, token }).health();
      setHealth(result);
      if (result.auth_required && !result.auth_ok) {
        setError('Connected, but the pairing token is wrong. Copy API_PAIRING_TOKEN from the server .env.');
        return false;
      }
      return true;
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err));
      return false;
    } finally {
      setTesting(false);
    }
  }

  async function save() {
    if (await test()) {
      await setConfig({ apiUrl: normalizeUrl(apiUrl), token: token.trim() });
      router.back();
    }
  }

  return (
    <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined} className="flex-1 bg-bg">
      <ScrollView contentContainerClassName="gap-5 p-4 pb-12" keyboardShouldPersistTaps="handled">
        <Text className="text-body text-text-muted">
          The AI runs on your computer. Start the server there, then enter its address on your Wi-Fi network
          (not localhost), for example http://192.168.1.23:8000.
        </Text>

        <View className="gap-2">
          <Text className="text-label text-text">Server address</Text>
          <TextInput
            value={apiUrl}
            onChangeText={setApiUrl}
            placeholder="http://192.168.1.23:8000"
            placeholderTextColor={colors.textMuted}
            autoCapitalize="none"
            autoCorrect={false}
            keyboardType="url"
            accessibilityLabel="Server address"
            className="min-h-[48px] rounded-sm border border-border bg-surface px-3 text-body text-text"
          />
        </View>

        <View className="gap-2">
          <Text className="text-label text-text">Pairing token</Text>
          <TextInput
            value={token}
            onChangeText={setToken}
            placeholder="Only if the server sets API_PAIRING_TOKEN"
            placeholderTextColor={colors.textMuted}
            autoCapitalize="none"
            autoCorrect={false}
            secureTextEntry
            accessibilityLabel="Pairing token"
            className="min-h-[48px] rounded-sm border border-border bg-surface px-3 text-body text-text"
          />
        </View>

        {error && <ErrorBanner message={error} />}

        {health && (
          <Card className="gap-3">
            <Text className="text-label text-text">
              {health.ready ? 'Everything is ready' : 'Connected, but some engines need attention'}
            </Text>
            {(Object.keys(ENGINE_LABELS) as (keyof Health['engines'])[]).map((key) => {
              const engine = health.engines[key];
              return (
                <View key={key} className="flex-row gap-3">
                  <Ionicons
                    name={engine.ok ? 'checkmark-circle' : 'close-circle'}
                    size={20}
                    color={engine.ok ? colors.success : colors.danger}
                  />
                  <View className="flex-1">
                    <Text className="text-body text-text">{ENGINE_LABELS[key]}</Text>
                    <Text className="text-caption text-text-muted">{engine.detail}</Text>
                  </View>
                </View>
              );
            })}
          </Card>
        )}

        <View className="gap-3">
          <Button title="Save" icon="checkmark" onPress={save} loading={testing} disabled={!apiUrl.trim()} />
          <Button title="Test connection" variant="secondary" onPress={test} disabled={testing || !apiUrl.trim()} />
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
