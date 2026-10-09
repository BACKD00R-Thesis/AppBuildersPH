import AsyncStorage from '@react-native-async-storage/async-storage';
import { createContext, type ReactNode, use, useEffect, useMemo, useState } from 'react';

import { type Api, createApi, type ServerConfig } from '@/lib/api';

const STORAGE_KEY = 'server-config';

const DEFAULT_CONFIG: ServerConfig = {
  apiUrl: process.env.EXPO_PUBLIC_API_URL ?? '',
  token: process.env.EXPO_PUBLIC_API_PAIRING_TOKEN ?? '',
};

interface ServerContextValue {
  config: ServerConfig;
  setConfig: (config: ServerConfig) => Promise<void>;
  api: Api;
  /** False until the saved config has been read from storage. */
  loaded: boolean;
}

const ServerContext = createContext<ServerContextValue | null>(null);

export function ServerProvider({ children }: { children: ReactNode }) {
  const [config, setConfigState] = useState<ServerConfig>(DEFAULT_CONFIG);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    AsyncStorage.getItem(STORAGE_KEY)
      .then((raw) => {
        if (raw) setConfigState({ ...DEFAULT_CONFIG, ...JSON.parse(raw) });
      })
      .catch(() => {
        // unreadable storage: keep defaults
      })
      .finally(() => setLoaded(true));
  }, []);

  const value = useMemo<ServerContextValue>(
    () => ({
      config,
      loaded,
      api: createApi(config),
      async setConfig(next) {
        setConfigState(next);
        await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      },
    }),
    [config, loaded],
  );

  return <ServerContext value={value}>{children}</ServerContext>;
}

export function useServer(): ServerContextValue {
  const value = use(ServerContext);
  if (!value) throw new Error('useServer must be used inside <ServerProvider>');
  return value;
}
