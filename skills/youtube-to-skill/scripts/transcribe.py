"""Transcribe audio/video to .srt + .txt next to the input file.

Usage: python transcribe.py <file> [--lang en] [--cpu]

Model: faster-whisper large-v3, downloaded to the Hugging Face cache on first run (~3 GB).
Set WHISPER_MODEL to a model name or a local folder to use something else.
"""
import argparse
import os
import sys
from pathlib import Path

MODEL = os.environ.get("WHISPER_MODEL", "large-v3")


def add_cuda_dlls():
    # pip's nvidia-cublas/cudnn wheels put DLLs in site-packages/nvidia/*/bin; Windows won't find them otherwise.
    if os.name != "nt":
        return
    import importlib.util
    spec = importlib.util.find_spec("nvidia")
    if not spec:
        return
    for root in spec.submodule_search_locations:
        for bin_dir in Path(root).glob("*/bin"):
            os.add_dll_directory(str(bin_dir))
            os.environ["PATH"] = str(bin_dir) + os.pathsep + os.environ["PATH"]


def ts(seconds):
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02}:{m:02}:{s:02},{ms:03}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("file")
    p.add_argument("--lang", default=None, help="e.g. en, nl; default auto-detect")
    p.add_argument("--cpu", action="store_true", help="force CPU even if an NVIDIA GPU is available")
    a = p.parse_args()

    src = Path(a.file)
    if not src.is_file():
        sys.exit(f"Not found: {src}")

    add_cuda_dlls()
    from faster_whisper import WhisperModel

    # "auto" picks CUDA when an NVIDIA GPU is usable, else CPU, and the fastest compute type for it.
    model = WhisperModel(MODEL, device="cpu" if a.cpu else "auto", compute_type="auto")

    segments, info = model.transcribe(str(src), language=a.lang, vad_filter=True)
    print(f"Language: {info.language} ({info.language_probability:.0%}), duration {info.duration:.0f}s")

    srt, txt = [], []
    for i, seg in enumerate(segments, 1):
        text = seg.text.strip()
        print(f"[{ts(seg.start)}] {text}")
        srt.append(f"{i}\n{ts(seg.start)} --> {ts(seg.end)}\n{text}\n")
        txt.append(text)

    src.with_suffix(".srt").write_text("\n".join(srt), encoding="utf-8")
    src.with_suffix(".txt").write_text("\n".join(txt) + "\n", encoding="utf-8")
    print(f"Wrote {src.with_suffix('.srt')} and .txt")


if __name__ == "__main__":
    main()
