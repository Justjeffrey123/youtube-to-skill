# youtube-to-skill

A Claude Code skill that turns a YouTube video into a Claude skill.
Paste a link, and Claude downloads the video, transcribes it locally with faster-whisper, screenshots the moments where something is shown on screen, and writes a `SKILL.md` from what the video teaches.

Tutorials are full of techniques you'd want Claude to know, and having Claude watch a video through screenshots burns tokens for nothing.
Transcription runs on your own machine, so Claude only pays for reading the transcript: about 5k tokens for an 18 minute video.

## What you get

- A new skill in `.claude/skills/<name>/SKILL.md` with the core idea, mistakes to avoid, numbered steps and a checklist.
- The text is rewritten as instructions, not a pasted transcript. Sponsor reads, sale plugs and intros are dropped.
- Names and jargon that speech recognition gets wrong are fixed from context and from what's on screen.
- Anything Claude isn't sure about ends up in a list at the end, with a link that jumps to that moment in the video:

```
- [07:12](https://www.youtube.com/watch?v=VIDEO_ID&t=430s) heard "recx 709" - my guess: Rec.709. What is it?
```

You answer, and Claude updates the skill.

## How it works

Measured on one 18 minute tutorial:

| Method | Claude tokens | Notes |
|---|---|---|
| Whisper on the audio (this skill) | ~5k | Gets names and jargon right |
| YouTube auto-captions, cleaned | ~5.5k | Mangled names and terms |
| Raw caption file | ~42k | Every line is repeated |
| One video frame every 30 s | ~55k | Mostly frames of nothing new |

Tutorials show a lot they never say out loud, like "set it to something like this".
So the skill reads the transcript first, finds the moments where the speaker points at the screen, and grabs a screenshot of just those moments with ffmpeg.
That's about 10-15 frames per 20 minutes instead of hundreds.
Claude reads them and writes the exact menu paths, values and panel layouts into the skill.
The same frames often settle a misheard term, because the real spelling is on screen.

## Requirements

- Python 3.9 or newer.
- `yt-dlp` and `ffmpeg`.
- About 3 GB of disk for the Whisper model, downloaded on first run.
- Optional: an NVIDIA GPU. Without one, transcription runs on the CPU with the same accuracy.
  On a Ryzen 9 5900HX the CPU took about 1.6x as long as an RTX 3070 Laptop GPU.
  Integrated AMD and Intel graphics aren't supported by faster-whisper, so those machines use the CPU.

## Install

The skill:

```
npx skills add Justjeffrey123/youtube-to-skill -g
```

The tools, on Windows:

```
winget install --id yt-dlp.yt-dlp -e
winget install --id Gyan.FFmpeg -e
py -m pip install -U faster-whisper "av<16"
```

On macOS:

```
brew install yt-dlp ffmpeg
python3 -m pip install -U faster-whisper "av<16"
```

On Debian or Ubuntu:

```
sudo apt install ffmpeg
python3 -m pip install -U yt-dlp faster-whisper "av<16"
```

For an NVIDIA GPU, also install the CUDA libraries:

```
pip install nvidia-cublas-cu12 "nvidia-cudnn-cu12==9.*"
```

`av<16` is pinned on purpose.
Newer PyAV versions break faster-whisper 1.2.1 with `open() got an unexpected keyword argument 'metadata_errors'`.

The large-v3 model downloads to the Hugging Face cache the first time you transcribe.
To use a model you already have, set `WHISPER_MODEL` to its folder or to another model name such as `medium`.

## Use

In Claude Code:

```
/youtube-to-skill https://www.youtube.com/watch?v=VIDEO_ID
```

A local file works too: an MP4, MP3 or anything else ffmpeg reads.

YouTube sometimes blocks downloads with `HTTP Error 403`.
The skill doesn't try to get around that.
It stops and asks you to download the video yourself, then continues from the file.

The transcription script also works on its own:

```
python skills/youtube-to-skill/scripts/transcribe.py video.mp4 --lang en
```

It writes `video.srt` and `video.txt` next to the input.
Add `--cpu` to skip the GPU.

## Respect the creators

Skills made this way summarize someone else's teaching.
The skill credits the creator and links the video by default; keep it that way.
Downloading from YouTube may go against YouTube's terms of service, so use it for your own reference.

## License

MIT
