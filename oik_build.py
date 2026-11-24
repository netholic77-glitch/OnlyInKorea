# -*- coding: utf-8 -*-
"""
Only in Korea - landscape long-form builder (1920x1080)

    python oik_build.py ep01.json            # TTS -> frames -> clips -> mp4 + srt + thumb + desc
    python oik_build.py ep01.json --skip-tts # reuse audio

Adapted from kankoku/scripts/build_episode.py (vertical shorts).
Narration subtitles are NOT burned in; an .srt is written for YouTube CC upload.
Only `emph` captions and the Hangul word badge are burned.
"""
import argparse, asyncio, io, json, os, re, shutil, subprocess, sys

import edge_tts
from mutagen.mp3 import MP3
import imageio_ffmpeg
from PIL import Image, ImageDraw, ImageFont

FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()
W, H = 1920, 1080
PAD = 0.45  # silence after each segment (s)

PAPER  = (239, 230, 214)
INK    = (31, 42, 58)
ACCENT = (232, 133, 58)
MUTED  = (127, 147, 168)
DIM    = (150, 140, 125)

F_BOLD = "C:/Windows/Fonts/segoeuib.ttf"
F_REG  = "C:/Windows/Fonts/segoeui.ttf"
F_KO   = "C:/Windows/Fonts/malgunbd.ttf"


def font(path, size):
    return ImageFont.truetype(path, size)


def tw(f, text):
    b = f.getbbox(text)
    return b[2] - b[0]


def fit(path, text, size, max_w, min_size=28):
    while size > min_size and tw(font(path, size), text) > max_w:
        size -= 4
    return font(path, size)


def center(d, text, y, f, fill):
    d.text(((W - tw(f, text)) // 2, y), text, font=f, fill=fill)


def paper_bg():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)
    # subtle torn-paper strip at top and bottom
    d.rectangle([0, 0, W, 18], fill=INK)
    d.rectangle([0, H - 18, W, H], fill=INK)
    return img, d


# ---------------------------------------------------------------- diagrams
def r_list(c, out):
    img, d = paper_bg()
    center(d, c["title"], 110, fit(F_BOLD, c["title"], 78, W - 300), INK)
    d.line([(360, 230), (W - 360, 230)], fill=ACCENT, width=5)
    items = c["items"]
    gap = 125 if len(items) <= 3 else 105
    y = 290 + (4 - len(items)) * 25
    fi = font(F_REG, 54)
    for it in items:
        d.ellipse([440, y + 22, 468, y + 50], fill=ACCENT)
        d.text((500, y), it, font=fi, fill=INK)
        y += gap
    img.save(out)


def r_timeline(c, out):
    img, d = paper_bg()
    center(d, c["title"], 110, fit(F_BOLD, c["title"], 74, W - 300), INK)
    pts = c["points"]
    x0, x1, ly = 220, W - 220, 440
    d.line([(x0, ly), (x1, ly)], fill=INK, width=6)
    step = (x1 - x0) / (len(pts) - 1)
    fh, fl = font(F_BOLD, 44), font(F_REG, 38)
    for i, (head, label) in enumerate(pts):
        x = int(x0 + i * step)
        last = i == len(pts) - 1
        col = ACCENT if last else INK
        d.ellipse([x - 22, ly - 22, x + 22, ly + 22], fill=col)
        d.text((x - tw(fh, head) // 2, ly - 110), head, font=fh, fill=col)
        words = label.split()
        lines, cur = [], ""
        for w_ in words:
            t = (cur + " " + w_).strip()
            if tw(fl, t) > 430 and cur:
                lines.append(cur); cur = w_
            else:
                cur = t
        lines.append(cur)
        for k, ln in enumerate(lines):
            d.text((x - tw(fl, ln) // 2, ly + 60 + k * 52), ln, font=fl, fill=INK)
    img.save(out)


def r_compare(c, out):
    # everything stays above SUB_TOP: the bottom band belongs to burned subtitles
    img, d = paper_bg()
    mid = W // 2
    d.line([(mid, 120), (mid, 640)], fill=DIM, width=3)
    fh = font(F_BOLD, 64)
    for side, x0, col in ((c["left"], 0, MUTED), (c["right"], mid, ACCENT)):
        cx = x0 + mid // 2
        d.text((cx - tw(fh, side["title"]) // 2, 130), side["title"], font=fh, fill=col)
        y = 280
        for ln in side["lines"]:
            f_ = fit(F_REG, ln, 50, mid - 160)
            d.text((cx - tw(f_, ln) // 2, y), ln, font=f_, fill=INK)
            y += 115
    v = c.get("verdict")
    if v:
        d.line([(500, 680), (W - 500, 680)], fill=ACCENT, width=4)
        center(d, v, 700, font(F_BOLD, 56), ACCENT)
    img.save(out)


def r_title(c, out):
    img, d = paper_bg()
    center(d, c["title"], 360, fit(F_BOLD, c["title"], 110, W - 240), INK)
    center(d, c.get("subtitle", ""), 520, font(F_BOLD, 84), ACCENT)
    d.line([(700, 660), (W - 700, 660)], fill=MUTED, width=4)
    img.save(out)


def r_reversal(c, out):
    img, d = paper_bg()
    f1 = fit(F_REG, c["strike"], 70, W - 300)
    x = (W - tw(f1, c["strike"])) // 2
    d.text((x, 340), c["strike"], font=f1, fill=DIM)
    d.line([(x - 15, 385), (x + tw(f1, c["strike"]) + 15, 385)], fill=ACCENT, width=7)
    center(d, c["punch"], 540, fit(F_BOLD, c["punch"], 92, W - 240), ACCENT)
    img.save(out)


def r_end(c, out):
    img, d = paper_bg()
    center(d, c["channel"], 330, font(F_BOLD, 120), INK)
    d.line([(660, 500), (W - 660, 500)], fill=ACCENT, width=6)
    center(d, c.get("line", ""), 540, font(F_REG, 52), MUTED)
    img.save(out)


CARDS = {"title": r_title, "reversal": r_reversal, "end": r_end}
DIAGRAMS = {"list": r_list, "timeline": r_timeline, "compare": r_compare}


def fit_image(src, dst):
    im = Image.open(src).convert("RGB")
    s, t = im.width / im.height, W / H
    if s > t:
        w = int(im.height * t); im = im.crop(((im.width - w) // 2, 0, (im.width + w) // 2, im.height))
    elif s < t:
        h = int(im.width / t); im = im.crop((0, (im.height - h) // 2, im.width, (im.height + h) // 2))
    # crop 3% to drop generator signature noise in the corner
    m = int(im.width * 0.03)
    im = im.crop((m, int(m * H / W), im.width - m, im.height - int(m * H / W)))
    im.resize((W, H), Image.LANCZOS).save(dst)


# ---------------------------------------------------------------- helpers
def run(args):
    r = subprocess.run(args, capture_output=True)
    if r.returncode:
        print(r.stderr.decode("utf-8", "ignore")[-2500:], file=sys.stderr)
        raise SystemExit("ffmpeg failed")


def apath(adir, s, voice, rate):
    # named by content so inserting/reordering segments never mismatches audio
    import hashlib
    return os.path.join(adir, hashlib.sha1(f"{voice}|{rate}|{s['text']}".encode()).hexdigest()[:12] + ".mp3")


async def tts_all(segs, voice, rate, adir):
    os.makedirs(adir, exist_ok=True)
    # sequential with retries: parallel requests intermittently return NoAudioReceived
    for i, s in enumerate(segs, 1):
        p = apath(adir, s, voice, rate)
        if os.path.exists(p) and os.path.getsize(p) > 1000:
            continue
        for k in range(8):
            try:
                await edge_tts.Communicate(s["text"], voice, rate=rate).save(p)
                if os.path.exists(p) and os.path.getsize(p) > 1000:
                    await asyncio.sleep(0.5)
                    break
            except Exception as e:
                print(f"  seg{i:02d} retry {k + 1}: {type(e).__name__}")
                if os.path.exists(p) and os.path.getsize(p) <= 1000:
                    try:
                        os.remove(p)
                    except:
                        pass
                await asyncio.sleep(2 * (k + 1))
        else:
            raise SystemExit(f"TTS failed: seg{i:02d}")


def clip(frame, audio, out, idx, still):
    dur = MP3(audio).info.length + PAD
    if still:
        vf = "scale=1920:1080,setsar=1,format=yuv420p"
    else:
        n = int(dur * 30)
        inc = 0.10 / max(n, 1)
        z = f"min(1.0+{inc:.6f}*on,1.10)" if idx % 2 else f"max(1.10-{inc:.6f}*on,1.0)"
        vf = (f"scale=2880:1620,zoompan=z='{z}':d=1:x='iw/2-(iw/zoom/2)':"
              f"y='ih/2-(ih/zoom/2)':s={W}x{H}:fps=30,setsar=1,format=yuv420p")
    run([FFMPEG, "-y", "-loop", "1", "-framerate", "30", "-t", f"{dur:.3f}", "-i", frame,
         "-i", audio, "-vf", vf, "-af", f"apad=pad_dur={PAD}", "-t", f"{dur:.3f}",
         "-c:v", "libx264", "-preset", "veryfast", "-crf", "19",
         "-c:a", "aac", "-b:a", "192k", "-ar", "48000", out])
    return dur


def ts(t, srt=False):
    h, m, s = int(t // 3600), int(t % 3600 // 60), t % 60
    if srt:
        return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s - int(s)) * 1000)) % 1000:03d}"
    return f"{h}:{m:02d}:{s:05.2f}"


# Burned subtitles: sized for phones, kept out of YouTube's fullscreen control bar.
SUB_SIZE = 70          # px on 1080p
SUB_LINE = 42          # max characters per line
SUB_MARGIN_V = 90      # bottom ~8%: progress bar / buttons appear below this on mobile
# two lines occupy roughly y 830-990, so diagrams keep their text above ~800


def _lines(text, limit=SUB_LINE):
    words, lines, cur = text.split(), [], ""
    for w_ in words:
        t = (cur + " " + w_).strip()
        if len(t) > limit and cur:
            lines.append(cur); cur = w_
        else:
            cur = t
    if cur:
        lines.append(cur)
    return lines


def _balance(lines):
    """Re-split two lines so they are similar in length (reads better than long+stub)."""
    if len(lines) != 2:
        return lines
    words = " ".join(lines).split()
    best = min(range(1, len(words)),
               key=lambda k: abs(len(" ".join(words[:k])) - len(" ".join(words[k:]))))
    a, b = " ".join(words[:best]), " ".join(words[best:])
    return [a, b] if max(len(a), len(b)) <= SUB_LINE else lines


SUB_DISPLAY = {}   # spoken form -> on-screen form (spec["sub_replace"]), e.g. "twenty twenty-six" -> "2026"


def display(text):
    for k in sorted(SUB_DISPLAY, key=len, reverse=True):
        text = text.replace(k, SUB_DISPLAY[k])
    return text


def sub_chunks(text):
    """Sentence -> screens of at most 2 lines, split evenly (no one-word orphan screens).
    Returns list of (text_len, [lines])."""
    out = []
    for sent in [p for p in re.split(r"(?<=[.?!])\s+", display(text)) if p]:
        words = sent.split()
        for k in range(1, len(words) + 1):
            target = len(sent) / k
            parts, cur = [], []
            for w_ in words:
                if cur and len(" ".join(cur + [w_])) > target * 1.08 and len(parts) < k - 1:
                    parts.append(" ".join(cur)); cur = [w_]
                else:
                    cur.append(w_)
            parts.append(" ".join(cur))
            screens = [_balance(_lines(p)) for p in parts]
            if all(len(sc) <= 2 for sc in screens):
                break
        out += [(len(" ".join(sc)), sc) for sc in screens]
    return out


def timed_subs(segs, durs):
    t = 0.0
    for s, d in zip(segs, durs):
        ch = sub_chunks(s["text"])
        total = sum(n for n, _ in ch) or 1
        tt = t
        for n, lines in ch:
            dd = (d - PAD) * n / total
            yield tt, tt + dd, lines
            tt += dd
        t += d


def write_srt(segs, durs, path):
    out = [f"{i}\n{ts(a, True)} --> {ts(b, True)}\n" + "\n".join(ls) + "\n"
           for i, (a, b, ls) in enumerate(timed_subs(segs, durs), 1)]
    io.open(path, "w", encoding="utf-8").write("\n".join(out))


def write_ass(segs, durs, path):
    head = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Emph,Segoe UI,64,&H00FFFFFF,&H00FFFFFF,&H003A2A1F,&H803A2A1F,-1,0,0,0,100,100,0,0,3,18,0,7,70,70,60,1
Style: Ko,Malgun Gothic,58,&H00FFFFFF,&H00FFFFFF,&H003A85E8,&H003A85E8,-1,0,0,0,100,100,0,0,3,16,0,9,70,70,60,1
Style: Sub,Segoe UI Semibold,{SUB_SIZE},&H00FFFFFF,&H00FFFFFF,&H00101010,&H99101010,-1,0,0,0,100,100,0,0,1,4,2,2,160,160,{SUB_MARGIN_V},1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
    ev = [f"Dialogue: 0,{ts(a)},{ts(b)},Sub,,0,0,0,," + r"\N".join(ls)
          for a, b, ls in timed_subs(segs, durs)]
    t = 0.0
    for s, d in zip(segs, durs):
        if s.get("emph"):
            ev.append(f"Dialogue: 1,{ts(t + 0.2)},{ts(t + min(4.0, d - 0.2))},Emph,,0,0,0,,{s['emph']}")
        if s.get("ko"):
            txt = s["ko"] + (r"{\fnSegoe UI\fs44}  " + s["ko_roman"] if s.get("ko_roman") else "")
            ev.append(f"Dialogue: 2,{ts(t + 0.2)},{ts(t + d - 0.2)},Ko,,0,0,0,,{txt}")
        t += d
    io.open(path, "w", encoding="utf-8-sig").write(head + "\n".join(ev) + "\n")


def make_thumb(spec, img_dir, out):
    th = spec["thumb"]
    im = Image.open(os.path.join(img_dir, th["img"])).convert("RGB")
    im = im.resize((1280, int(im.height * 1280 / im.width)))
    im = im.crop((0, 0, 1280, 720))
    d = ImageDraw.Draw(im, "RGBA")
    d.rectangle([0, 0, 720, 720], fill=(31, 42, 58, 175))
    d.text((60, 190), th["kicker"], font=font(F_BOLD, 120), fill=(255, 255, 255))
    d.text((60, 340), th["punch"], font=font(F_BOLD, 120), fill=ACCENT)
    im.save(out, quality=92)


def make_desc(spec, durs, out):
    ds = spec["desc"]
    # chapter times: first segment index whose text starts each chapter (fixed map)
    starts = spec.get("chapter_segments", [])
    times, t = [], 0.0
    for d in durs:
        times.append(t); t += d
    lines = [spec["title"], "", ds["lead"], "",
             "This channel explains how systems in Korea work. No politics, no rankings between countries.", ""]
    if starts:
        lines.append("Chapters")
        for (seg_i, (_, name)) in zip(starts, ds["chapters"]):
            s = int(times[seg_i - 1])
            lines.append(f"{s // 60}:{s % 60:02d} {name}")
        lines.append("")
    lines.append("Sources")
    lines += ["- " + r for r in ds["refs"]]
    lines += ["", "Visuals are AI-generated paper-craft illustrations. Narration voice is synthetic.", "",
              " ".join("#" + x.replace(" ", "") for x in ds["tags"][:5]), "",
              "Tags: " + ", ".join(ds["tags"])]
    io.open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec")
    ap.add_argument("--skip-tts", action="store_true")
    a = ap.parse_args()
    sp = os.path.abspath(a.spec)
    base = os.path.dirname(sp)
    spec = json.load(io.open(sp, encoding="utf-8"))
    SUB_DISPLAY.update(spec.get("sub_replace", {}))
    segs = spec["segments"]
    ep = spec["episode"]
    adir = os.path.join(base, spec["audio_dir"])
    idir = os.path.join(base, spec["images_dir"])
    work = os.path.join(base, f"ep{ep:02d}_work")
    shutil.rmtree(work, ignore_errors=True); os.makedirs(work)

    if not a.skip_tts:
        print("TTS ..."); asyncio.run(tts_all(segs, spec["voice"], spec["rate"], adir))

    clips, durs = [], []
    for i, s in enumerate(segs, 1):
        fr = os.path.join(work, f"fr{i:02d}.png")
        still = True
        if s.get("img"):
            fit_image(os.path.join(idir, s["img"]), fr); still = False
        elif s.get("diagram"):
            DIAGRAMS[s["diagram"]["kind"]](s["diagram"], fr)
        elif s.get("card"):
            CARDS[s["card"]["kind"]](s["card"], fr)
        c = os.path.join(work, f"clip{i:02d}.mp4")
        durs.append(clip(fr, apath(adir, s, spec["voice"], spec["rate"]), c, i, still))
        clips.append(c)
        print(f"  clip {i:02d} {durs[-1]:5.1f}s")

    lst = os.path.join(work, "list.txt")
    io.open(lst, "w", encoding="utf-8").write("".join(f"file '{c.replace(chr(92), '/')}'\n" for c in clips))
    joined = os.path.join(work, "joined.mp4")
    run([FFMPEG, "-y", "-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", joined])

    ass = os.path.join(work, "emph.ass")
    write_ass(segs, durs, ass)
    out = os.path.join(base, spec["out"])
    ass_f = ass.replace("\\", "/").replace(":", "\\:")
    run([FFMPEG, "-y", "-i", joined, "-vf", f"ass='{ass_f}'", "-c:v", "libx264", "-preset", "medium",
         "-crf", "19", "-c:a", "copy", "-movflags", "+faststart", out])

    stem = os.path.splitext(out)[0]
    write_srt(segs, durs, stem + ".en.srt")
    make_thumb(spec, idir, stem + "_thumb.jpg")
    make_desc(spec, durs, stem + "_description.txt")
    tot = sum(durs)
    print(f"\nDONE {os.path.basename(out)}  {int(tot // 60)}:{int(tot % 60):02d}  "
          f"{os.path.getsize(out) / 1e6:.0f} MB")


if __name__ == "__main__":
    main()
