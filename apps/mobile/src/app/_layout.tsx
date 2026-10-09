import '@/global.css';

import { DarkTheme, Stack, ThemeProvider } from 'expo-router';
import * as SplashScreen from 'expo-splash-screen';
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';

import { colors } from '@/components/ui';
import { ServerProvider, useServer } from '@/lib/server';

SplashScreen.preventAutoHideAsync();

const theme = {
  ...DarkTheme,
  colors: {
    ...DarkTheme.colors,
    background: colors.bg,
    card: colors.bg,
    primary: colors.primary,
    text: colors.text,
  },
};

function AppStack() {
  const { loaded } = useServer();
  useEffect(() => {
    if (loaded) SplashScreen.hideAsync();
  }, [loaded]);
  if (!loaded) return null;

  return (
    <Stack
      screenOptions={{
        headerStyle: { backgroundColor: colors.bg },
        headerTintColor: colors.text,
        headerShadowVisible: false,
        contentStyle: { backgroundColor: colors.bg },
      }}>
      <Stack.Screen name="index" options={{ title: 'Brainrot Study' }} />
      <Stack.Screen name="settings" options={{ title: 'Server', presentation: 'modal' }} />
      <Stack.Screen name="new" options={{ title: 'New video' }} />
      <Stack.Screen name="project/[id]/index" options={{ title: 'Script' }} />
      <Stack.Screen name="project/[id]/style" options={{ title: 'Style' }} />
      <Stack.Screen name="render/[id]" options={{ title: 'Render' }} />
      <Stack.Screen name="watch" options={{ title: '', headerTransparent: true }} />
    </Stack>
  );
}

export default function RootLayout() {
  return (
    <ThemeProvider value={theme}>
      <ServerProvider>
        <StatusBar style="light" />
        <AppStack />
      </ServerProvider>
    </ThemeProvider>
  );
}
