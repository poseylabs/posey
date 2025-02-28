# Posey TTS
We have a TTS API the is setup to support any TTS service with an extendable adapter interface.

Currently, we just have an initial adapter for [ElevenLabs](https://elevenlabs.io/).

Eventually, we will add more adapters for other TTS services, including self-hosted services.

## ElevenLabs

[elevenlabs-js](https://github.com/elevenlabs/elevenlabs-js)

elevenlabs-js requires [MPV](https://mpv.io/) and [ffmpeg](https://ffmpeg.org/):

```bash
brew install mpv ffmpeg
```