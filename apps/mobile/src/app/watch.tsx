import { router, Stack, useLocalSearchParams } from 'expo-router';
import * as Sharing from 'expo-sharing';
import { useVideoPlayer, VideoView } from 'expo-video';
import { Alert, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { IconButton } from '@/components/ui';
import { deleteSaved, listSaved } from '@/lib/library';

/** Full-screen player for a video saved on the phone. */
export default function WatchScreen() {
  const { uri, title } = useLocalSearchParams<{ uri: string; title?: string }>();
  const player = useVideoPlayer(uri, (p) => {
    p.loop = true;
    p.play();
  });

  function remove() {
    Alert.alert('Delete from this phone?', 'The project stays on the server, so you can save it again.', [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: () => {
          const video = listSaved().find((v) => v.uri === uri);
          if (video) deleteSaved(video.renderId);
          router.back();
        },
      },
    ]);
  }

  return (
    <View className="flex-1 bg-black">
      <Stack.Screen
        options={{
          title: '',
          headerRight: () => (
            <View className="flex-row">
              <IconButton
                icon="share-outline"
                label="Share video"
                onPress={() => Sharing.shareAsync(uri, { mimeType: 'video/mp4', dialogTitle: title })}
              />
              <IconButton icon="trash-outline" label="Delete video from phone" onPress={remove} />
            </View>
          ),
        }}
      />
      <SafeAreaView className="flex-1">
        <VideoView player={player} style={{ flex: 1 }} contentFit="contain" nativeControls fullscreenOptions={{ enable: true }} />
      </SafeAreaView>
    </View>
  );
}
