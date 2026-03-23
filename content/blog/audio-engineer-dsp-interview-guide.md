---
title: "Audio Engineer and DSP Developer Interview Guide"
description: "Technical interview preparation for audio engineering and DSP roles: digital signal processing fundamentals, audio plugin development (VST/AU/AAX), real-time audio constraints, spatial audio, and what companies like Apple, Dolby, Spotify, and audio software companies expect."
date: "2026-03-19"
category: "Specialty Engineering Roles"
---

# Audio Engineer and DSP Developer Interview Guide

Audio engineering is one of the most specialized software disciplines — the intersection of signal processing mathematics, real-time constraints, and perceptual psychology. Companies hiring audio engineers range from music software (Native Instruments, iZotope, Ableton), to spatial audio platforms (Dolby, Apple Spatial Audio, Meta Reality Labs), to streaming infrastructure (Spotify, Apple Music), to audio hardware (Bose, Sonos, Focusrite). Each segment has different technical focuses, but the foundation is shared.

## Where Audio Engineers Work

**Music software companies**: Ableton (Live), Native Instruments (Komplete), iZotope (Ozone, RX), Waves Audio, Steinberg (Cubase, parent company Yamaha), Avid (Pro Tools, Media Composer). Building DAW (Digital Audio Workstation) components, audio effects plugins, virtual instruments.

**Spatial audio and immersive**: Dolby (Atmos, Cinema), Apple (Spatial Audio, AirPods head tracking), Meta Reality Labs (audio for VR/AR), Sony 360 Reality Audio, Visisonics. Building binaural rendering, HRTF personalization, object-based audio systems.

**Consumer hardware**: Apple (AirPods firmware, Active Noise Cancellation algorithms), Bose (QuietComfort, ANC), Sonos (multi-room audio, room correction), Focusrite (audio interfaces), Shure. Emphasis on DSP firmware, adaptive algorithms, low-power processing.

**Streaming and content**: Spotify (audio quality, normalization, podcast processing), Apple Music (Lossless, Spatial Audio delivery), Amazon Music. Audio encoding pipelines, loudness normalization (EBU R128), dynamic range management.

**Game audio**: middleware companies (FMOD, Wwise/Audiokinetic) and game studio audio programmers. Real-time audio for interactive experiences, procedural audio, Ambisonics for VR.

## DSP Fundamentals That Interviews Test

**Sampling and the Nyquist theorem**: Audio is continuous; digital audio is discrete samples. Nyquist: to represent a signal of frequency f, you need a sample rate of at least 2f. CD-quality audio uses 44,100 Hz (capturing up to 22,050 Hz — above human hearing range of ~20,000 Hz). Why 44.1 kHz specifically? Legacy reasons from early digital-to-analog conversion hardware.

**The Discrete Fourier Transform (DFT) and FFT**: The Fast Fourier Transform computes the frequency content of a signal in O(n log n) instead of O(n²). Core to: spectral analysis, frequency-domain filtering (multiply by a filter kernel in frequency domain instead of convolution in time domain), pitch detection, pitch shifting.

**Filters**: FIR (Finite Impulse Response) filters — always stable, linear phase, computationally expensive; IIR (Infinite Impulse Response) filters — more efficient, can be unstable, non-linear phase (phase distortion can be audible). Biquad filters (second-order IIR) are the building block of most audio EQ and effects — know the cookbook formulae for lowpass, highpass, peak, shelf filters.

**Convolution**: Linear convolution in time domain = multiplication in frequency domain. Used for: reverb (convolve with an impulse response of a real room), FIR filtering, speaker/room correction.

**Audio compression and dynamics processing**: Compressors reduce dynamic range (ratio, threshold, attack, release, knee). Limiters are infinite-ratio compressors. Understanding these psychoacoustically (why we use them, not just how they work) signals genuine audio domain knowledge.

**Psychoacoustics basics**: How humans perceive sound affects audio algorithm design. A-weighting (frequency-dependent loudness perception), masking (a loud sound makes nearby quiet sounds inaudible — exploited in MP3/AAC encoding), binaural hearing (ITD — interaural time difference, ILD — interaural level difference for localization), HRTF (Head-Related Transfer Functions for spatial simulation).

## Real-Time Audio Constraints

Audio processing has hard real-time constraints that differ from most software:

**Audio buffer and latency**: Audio interfaces process in buffers (typically 64–512 samples). At 44,100 Hz, a 128-sample buffer = 2.9ms latency. For live monitoring, latency above ~10ms is perceptible. This means: no allocation in the audio thread, no blocking operations, no system calls. The audio callback must complete in buffer time or you get a glitch (xrun/underrun).

**Lock-free audio thread communication**: The audio thread must not block on mutexes. To communicate between audio thread and UI thread, use lock-free queues (FIFO based on atomic compare-and-swap), wait-free structures, or double-buffering with atomic pointer swaps.

**Denormal numbers**: IEEE 754 floating-point denormals (very small numbers close to zero) cause significant CPU slowdown on some architectures because they're handled in software. Audio algorithms like filters can accumulate denormals over time. Solution: flush denormals to zero (FTZ/DAZ CPU flags) or add a small DC offset.

## Plugin Development

VST3/AU/AAX are the three major plugin APIs. Most companies use JUCE (C++ framework that abstracts across plugin formats and platforms) for development. Know: the processor/editor separation (audio processing in processor, UI in editor, they run in different threads), parameter automation (thread-safe parameter updates), preset management.

## How to Prepare

Build an audio plugin with JUCE — implement a basic EQ or compressor. Read "The Audio Programming Book" (Boulanger and Lazzarini). Study the cooking recipes in "Audio EQ Cookbook" (Bristow-Johnson). Implement an FFT-based pitch detector from scratch. For spatial audio roles, understand Ambisonic formats (B-format, higher order Ambisonics) and binaural rendering.

The combination of DSP math, real-time C++, and perceptual domain knowledge is rare — engineers who have all three are genuinely hard to find.
