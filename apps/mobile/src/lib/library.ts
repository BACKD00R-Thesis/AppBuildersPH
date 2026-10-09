/** Rendered videos downloaded to the phone, so they play without the server. */
import { Directory, File, Paths } from 'expo-file-system';
import { Platform } from 'react-native';

import type { Api, Render } from '@/lib/api';

export interface SavedVideo {
  renderId: string;
  projectId: string;
  title: string;
  uri: string;
  durationS: number | null;
  savedAt: string;
}

export const librarySupported = Platform.OS !== 'web';

function videosDir(): Directory {
  const dir = new Directory(Paths.document, 'videos');
  dir.create({ intermediates: true, idempotent: true });
  return dir;
}

function indexFile(): File {
  return new File(videosDir(), 'library.json');
}

function readIndex(): SavedVideo[] {
  if (!librarySupported) return [];
  const file = indexFile();
  if (!file.exists) return [];
  try {
    return JSON.parse(file.textSync()) as SavedVideo[];
  } catch {
    return [];
  }
}

function writeIndex(videos: SavedVideo[]): void {
  const file = indexFile();
  if (!file.exists) file.create();
  file.write(JSON.stringify(videos));
}

/** Saved videos whose files still exist, newest first. */
export function listSaved(): SavedVideo[] {
  return readIndex()
    .filter((video) => new File(video.uri).exists)
    .sort((a, b) => b.savedAt.localeCompare(a.savedAt));
}

export function findSaved(renderId: string): SavedVideo | undefined {
  return listSaved().find((video) => video.renderId === renderId);
}

export async function saveRender(
  api: Api,
  render: Render,
  title: string,
  onProgress?: (fraction: number) => void,
): Promise<SavedVideo> {
  if (!render.video_url) throw new Error("This video isn't ready yet.");
  const destination = new File(videosDir(), `${render.id}.mp4`);
  const file = await File.downloadFileAsync(api.mediaUrl(render.video_url), destination, {
    headers: api.headers,
    idempotent: true,
    onProgress: ({ bytesWritten, totalBytes }) => {
      if (totalBytes > 0) onProgress?.(bytesWritten / totalBytes);
    },
  });
  const video: SavedVideo = {
    renderId: render.id,
    projectId: render.project_id,
    title,
    uri: file.uri,
    durationS: render.duration_s,
    savedAt: new Date().toISOString(),
  };
  writeIndex([video, ...readIndex().filter((v) => v.renderId !== render.id)]);
  return video;
}

export function deleteSaved(renderId: string): void {
  const videos = readIndex();
  const video = videos.find((v) => v.renderId === renderId);
  if (video) {
    const file = new File(video.uri);
    if (file.exists) file.delete();
  }
  writeIndex(videos.filter((v) => v.renderId !== renderId));
}
