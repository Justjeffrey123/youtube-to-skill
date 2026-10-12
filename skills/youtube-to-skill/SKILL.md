---
name: youtube-to-skill
description: Turn a YouTube video (URL) or a local video/audio file into a Claude skill. Transcribes locally with faster-whisper large-v3, screenshots the relevant on-screen moments with ffmpeg, then writes a SKILL.md in Claude's own words. Use when the user says "make this video into a skill", "/youtube-to-skill", or pastes a YouTube link and asks for a skill from it.
---

# YouTube video to Claude skill

Local transcription costs zero Claude tokens; only reading the transcript does (~5k tokens for 18 min).
Whisper beats YouTube auto-captions on names and jargon, so always transcribe the file.

## Tools

- `yt-dlp` and `ffmpeg` on PATH. On Windows, open a fresh shell after installing, or reload PATH in PowerShell:
  `$env:Path = [Environment]::GetEnvironmentVariable('Path','User')+';'+[Environment]::GetEnvironmentVariable('Path','Machine')`
- Python with `faster-whisper`. Use `py` on Windows, `python3` elsewhere.
- Whisper script, bundled with this skill: `python <this skill's folder>/scripts/transcribe.py <file> [--lang en] [--cpu]`
  Reads any audio or video ffmpeg can decode. Writes `<file>.srt` and `<file>.txt` next to the input.
  Uses an NVIDIA GPU when available, otherwise the CPU (same accuracy, a few times slower).
  The first run downloads the large-v3 model (~3 GB) to the Hugging Face cache. `WHISPER_MODEL` can point to another model name or a local folder.
  If it fails with `metadata_errors`: `pip install "av<16"`.

If a tool is missing, show the user the setup commands from this skill's README and ask before installing anything.

## Steps

1. **Work folder.** Create `yt2skill/<short-slug>/` in the current directory, unless the user names another place.
2. **Metadata** (title, channel, duration, language):
   `yt-dlp --skip-download --print "%(title)s | %(channel)s | %(duration_string)s | %(language)s" <url>`
3. **Get the media.** Default to a 720p MP4: Whisper reads it directly and step 6 needs the picture.
   `yt-dlp -f "bv*[height<=720]+ba/b[height<=720]" --merge-output-format mp4 -o "<folder>/video.%(ext)s" <url>`
   Audio only (`-f bestaudio -x --audio-format m4a`) only for talks or podcasts where nothing on screen matters.
   If yt-dlp fails (e.g. `HTTP Error 403`), do NOT try workarounds (cookies, player clients, PO tokens).
   Stop and ask the user to download the video themselves (MP4 720p; MP3 only for talks) and give the file path.
   Suggest a [cobalt](https://github.com/imputnet/cobalt) instance in their browser, such as https://cobalt.meowing.de/ or another cobalt community instance: open source, no ads.
   Do not drive cobalt or any other download site yourself: instances sit behind bot checks, and ad-filled converter sites are untrusted download sources.
   Any local file works as input.
4. **Transcribe.** Run the Whisper script with `--lang` set from the metadata.
   Use a long timeout: a few minutes per 20 minutes of audio on a GPU, longer on CPU.
   Save output to a log file instead of printing it to the conversation.
5. **Read `<file>.txt`** (no timestamps, cheapest). Use the `.srt` only to find a timestamp.
6. **Look at the relevant moments.** Tutorials show what they don't say. With an MP4, screenshot the moments that matter and read them (~1.5k tokens per frame).
   Pick timestamps from the `.srt` where the speaker points at the screen:
   - Vague references: "like this", "right here", "something like that", "this setting", "go in here".
   - Settings, values, menus, node or panel layouts, scopes, before/after comparisons.
   - Every unsure term from step 7: on-screen text, menus and titles often show the real spelling. Check the frame before asking the user.
   Grab each frame 1-2 seconds after the line starts (the action usually follows the words), into a `frames` subfolder:
   `ffmpeg -y -loglevel error -ss 00:07:14 -i video.mp4 -frames:v 1 -vf scale=1280:-1 frames/0714.png`
   Then read the PNGs and fold what you see into the skill: exact menu paths, slider values, which panel, what the result looks like.
   Budget about 10-15 frames per 20 minutes (~20k tokens). Never sample the whole video at fixed intervals.
   If a frame misses the moment, try 2-3 seconds later once, then move on.
   No MP4 (audio only): skip this step and mention in the report which moments would have needed the picture.
7. **Write the skill** to `.claude/skills/<kebab-name>/SKILL.md` in the current project, or `~/.claude/skills/<kebab-name>/SKILL.md` if the user wants it everywhere. Ask if unclear.
   - Frontmatter: `name` (kebab-case) and a `description` saying what it does AND when to use it (trigger words, software, symptoms).
   - Body: a source line (creator, title, video URL), the core idea, mistakes to avoid, numbered workflow steps, a checklist.
   - Rewrite in your own words as instructions. Do not paste the transcript or long quotes; at most one short quote.
   - Fix speech recognition errors in names and jargon (brands, software terms, the creator's name from metadata).
     When a term is unclear and the fix is a guess, write your best guess, mark it, and add it to the unsure list (step 8). Look up its timestamp in the `.srt`.
   - Drop sponsor reads, sale plugs, intros and outros.
8. **Report** to the user: skill path, slash command, what it covers, token cost of the transcript and how many frames you read.
   Keep the transcript files in the work folder; don't delete them.
   **End the report with the unsure terms**, as the very last thing, one per line:
   `- [mm:ss](https://www.youtube.com/watch?v=<ID>&t=<seconds>s) heard "<transcript text>" - my guess: <guess>. What is it?`
   `<seconds>` = timestamp in whole seconds (07:12 -> 432). Start the link 2 seconds early so the word is audible. For a local file without a URL, give the timecode only.
   Ask the user to confirm or correct, then update the SKILL.md with their answers. No unsure terms: say so in one line.

## Notes

- A skill made this way summarizes someone else's teaching. Always credit the creator and link the video.
- Downloading from YouTube may go against YouTube's terms of service. Use it for personal reference.
