/**
 * Audio utility functions for cross-browser compatibility.
 * Safari doesn't support WebM natively, so we need to detect and use appropriate formats.
 */

/**
 * Returns the best supported audio MIME type for the current browser.
 * Prefers WebM with Opus for Chrome/Firefox, falls back to MP4/WAV for Safari.
 */
export function getSupportedMimeType(): string {
  const types = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/mp4',
    'audio/ogg;codecs=opus',
    'audio/wav'
  ];

  for (const type of types) {
    if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported(type)) {
      return type;
    }
  }

  // Ultimate fallback
  return 'audio/wav';
}

/**
 * Detects if the current browser is Safari.
 */
export function isSafari(): boolean {
  if (typeof navigator === 'undefined') return false;
  return /^((?!chrome|android).)*safari/i.test(navigator.userAgent);
}

/**
 * Gets the file extension for a given MIME type.
 */
export function getExtensionForMimeType(mimeType: string): string {
  if (mimeType.includes('webm')) return 'webm';
  if (mimeType.includes('mp4')) return 'mp4';
  if (mimeType.includes('ogg')) return 'ogg';
  if (mimeType.includes('wav')) return 'wav';
  return 'webm'; // default
}

/**
 * Checks if MediaRecorder API is available in the current browser.
 */
export function isMediaRecorderSupported(): boolean {
  return typeof MediaRecorder !== 'undefined';
}
