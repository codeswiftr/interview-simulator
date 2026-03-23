/**
 * Voice quality assessment utilities for ranking browser TTS voices
 *
 * Quality is determined by:
 * 1. Known high-quality voice providers (Google, Microsoft Neural, Apple)
 * 2. Neural/enhanced voice indicators in the name
 * 3. English language preference for interview coaching
 */

export type VoiceQuality = 'premium' | 'standard';

/** Voice names known to be high-quality */
const PREMIUM_VOICE_PATTERNS = [
  // Google voices (high quality on Chrome)
  'Google UK English',
  'Google US English',
  'Google Australian English',

  // Microsoft voices (high quality on Edge/Windows)
  'Microsoft Zira',
  'Microsoft David',
  'Microsoft Mark',
  'Microsoft Aria',
  'Microsoft Jenny',

  // Apple voices (high quality on macOS/iOS)
  'Samantha',
  'Daniel',
  'Karen',
  'Moira',
  'Fiona',
  'Alex',

  // Neural voice indicators
  'Neural',
  'Enhanced',
  'Premium',
];

/** Voice names that indicate lower quality (system/default voices) */
const STANDARD_VOICE_INDICATORS = [
  'Compact',
  'Embedded',
  'Mobile',
];

/**
 * Assess the quality of a voice based on its name and characteristics
 */
export function getVoiceQuality(voice: SpeechSynthesisVoice): VoiceQuality {
  const name = voice.name.toLowerCase();

  // Check for standard/low quality indicators first
  if (STANDARD_VOICE_INDICATORS.some(indicator => name.includes(indicator.toLowerCase()))) {
    return 'standard';
  }

  // Check for premium voice patterns
  const isPremium = PREMIUM_VOICE_PATTERNS.some(pattern =>
    voice.name.includes(pattern)
  );

  return isPremium ? 'premium' : 'standard';
}

/**
 * Score a voice for ranking purposes (higher = better)
 */
export function getVoiceScore(voice: SpeechSynthesisVoice): number {
  let score = 0;

  // Quality tier bonus
  if (getVoiceQuality(voice) === 'premium') {
    score += 100;
  }

  // English language bonus
  if (voice.lang?.toLowerCase().startsWith('en')) {
    score += 50;
  }

  // US/UK English bonus (most natural for interviews)
  if (voice.lang === 'en-US' || voice.lang === 'en-GB') {
    score += 25;
  }

  // Local voice bonus (faster response)
  if (voice.localService) {
    score += 10;
  }

  // Google voices bonus (consistent quality)
  if (voice.name.includes('Google')) {
    score += 20;
  }

  // Microsoft Neural voices bonus
  if (voice.name.includes('Microsoft') && voice.name.includes('Neural')) {
    score += 15;
  }

  // Apple voices on macOS
  if (voice.name === 'Samantha' || voice.name === 'Daniel') {
    score += 15;
  }

  return score;
}

/**
 * Sort voices by quality (best first)
 */
export function sortVoicesByQuality(voices: SpeechSynthesisVoice[]): SpeechSynthesisVoice[] {
  return [...voices].sort((a, b) => getVoiceScore(b) - getVoiceScore(a));
}

/**
 * Get the recommended voice for the user
 */
export function getRecommendedVoice(voices: SpeechSynthesisVoice[]): SpeechSynthesisVoice | null {
  if (voices.length === 0) return null;

  const sorted = sortVoicesByQuality(voices);
  return sorted[0];
}

/**
 * Filter voices to only English voices
 */
export function getEnglishVoices(voices: SpeechSynthesisVoice[]): SpeechSynthesisVoice[] {
  return voices.filter(v => v.lang?.toLowerCase().startsWith('en'));
}

/**
 * Get premium English voices only
 */
export function getPremiumVoices(voices: SpeechSynthesisVoice[]): SpeechSynthesisVoice[] {
  return voices.filter(v => getVoiceQuality(v) === 'premium');
}

/**
 * Format voice for display with quality badge
 */
export function formatVoiceDisplay(voice: SpeechSynthesisVoice): {
  name: string;
  lang: string;
  quality: VoiceQuality;
  badge: string | null;
} {
  const quality = getVoiceQuality(voice);

  return {
    name: voice.name,
    lang: voice.lang,
    quality,
    badge: quality === 'premium' ? 'Premium' : null,
  };
}
