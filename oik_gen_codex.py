# -*- coding: utf-8 -*-
"""
Only in Korea - scene images via Codex built-in image generation (ChatGPT plan, no API billing).

    python oik_gen_codex.py ep01.json            # missing images only, 3 in parallel
    python oik_gen_codex.py ep01.json --only s05_desk.png --force

Uses the Codex desktop app's bundled codex.exe (the ~/.codex/.sandbox-bin copy lacks
codex-code-mode-host.exe, so its image tool fails). Generated files land in
~/.codex/generated_images/<session-id>/ and are copied to <images_dir>/<img>.
"""
import argparse, glob, importlib.util, io, json, os, re, shutil, subprocess, sys, time
from concurrent.futures import ThreadPoolExecutor

HOME = os.path.expanduser("~")
GEN = os.path.join(HOME, ".codex", "generated_images")
HERE = os.path.dirname(os.path.abspath(__file__))

spec_ = importlib.util.spec_from_file_location("g", os.path.join(HERE, "oik_gen_images.py"))
g = importlib.util.module_from_spec(spec_); spec_.loader.exec_module(g)


def codex_exe():
    c = sorted(glob.glob(os.path.join(HOME, "AppData", "Local", "OpenAI", "Codex", "bin", "*", "codex.exe")),
               key=os.path.getmtime)
    if not c:
        sys.exit("Codex app codex.exe not found")
    return c[-1]


TEMPLATE = ("Call your built-in image generation tool directly, exactly once. Do not run any shell "
            "commands and do not save files; just generate the image. Landscape orientation (1536x1024).\n\n"
            "Prompt: {p}")


def one(exe, prompt, dst, tries=3):
    for k in range(tries):
        r = subprocess.run([exe, "exec", "--skip-git-repo-check", "-s", "read-only", "-"],
                           input=TEMPLATE.format(p=prompt).encode("utf-8"),
                           capture_output=True, cwd=HERE, timeout=900)
        out = (r.stdout + r.stderr).decode("utf-8", "ignore")
        m = re.search(r"session id:\s*([0-9a-f-]{36})", out)
        files = sorted(glob.glob(os.path.join(GEN, m.group(1), "*.png")), key=os.path.getmtime) if m else []
        if files:
            shutil.copy2(files[-1], dst)
            return True
        print(f"    retry {k + 1} {os.path.basename(dst)}: {out.strip().splitlines()[-1][:120] if out.strip() else 'no output'}")
        time.sleep(20 * (k + 1))
    return False


BATCH_TEMPLATE = ("Call your built-in image generation tool exactly {n} times, once per prompt below, "
                  "strictly in the listed order, one call at a time. Do not run any shell commands and do "
                  "not save files. Every image is landscape (1536x1024). Do not change the prompts.\n\n{body}")


def batch(exe, jobs, out_dir):
    """One Codex session for several images: the ~30k-token session overhead is paid once.
    Files are matched to jobs by creation order; on a count mismatch nothing is copied."""
    body = "\n\n".join(f"Image {i}: {p}" for i, (_, p) in enumerate(jobs, 1))
    r = subprocess.run([exe, "exec", "--skip-git-repo-check", "-s", "read-only", "-"],
                       input=BATCH_TEMPLATE.format(n=len(jobs), body=body).encode("utf-8"),
                       capture_output=True, cwd=HERE, timeout=1800)
    out = (r.stdout + r.stderr).decode("utf-8", "ignore")
    m = re.search(r"session id:\s*([0-9a-f-]{36})", out)
    tok = re.search(r"tokens used\s*\n?\s*([\d,]+)", out)
    files = sorted(glob.glob(os.path.join(GEN, m.group(1), "*.png")), key=os.path.getmtime) if m else []
    print(f"  batch of {len(jobs)}: got {len(files)} images, tokens {tok.group(1) if tok else '?'}", flush=True)
    if len(files) != len(jobs):
        return [False] * len(jobs)
    for (name, _), f in zip(jobs, files):
        shutil.copy2(f, os.path.join(out_dir, name))
    return [True] * len(jobs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("spec"); ap.add_argument("--only"); ap.add_argument("--force", action="store_true")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--batch", type=int, default=0, help="images per Codex session (0 = one each)")
    a = ap.parse_args()
    sp = os.path.abspath(a.spec)
    spec = json.load(io.open(sp, encoding="utf-8"))
    out_dir = os.path.join(os.path.dirname(sp), spec["images_dir"]); os.makedirs(out_dir, exist_ok=True)
    jobs, seen = [], set()
    for s in spec["segments"]:
        if s.get("img") and s.get("prompt") and s["img"] not in seen:
            seen.add(s["img"])
            pre = g.STYLE_PRE_OBJECT if s.get("style") == "object" else g.STYLE_PRE
            jobs.append((s["img"], pre + s["prompt"] + g.STYLE_SUF))
    if a.only:
        jobs = [j for j in jobs if j[0] == a.only]
    todo = [j for j in jobs if a.force or not os.path.exists(os.path.join(out_dir, j[0]))]
    exe = codex_exe()
    print(f"codex: {exe}\n{len(todo)} images to make -> {out_dir}", flush=True)

    if a.batch > 1:
        groups = [todo[i:i + a.batch] for i in range(0, len(todo), a.batch)]
        with ThreadPoolExecutor(a.workers) as ex:
            res = sum(ex.map(lambda gr: batch(exe, gr, out_dir), groups), [])
        missing = [j[0] for j, ok in zip(todo, res) if not ok]
        print(f"\ndone {sum(res)}/{len(res)}" + (f"  missing: {missing}" if missing else ""))
        sys.exit(1 if missing else 0)

    def work(j):
        t0 = time.time()
        ok = one(exe, j[1], os.path.join(out_dir, j[0]))
        print(f"  {'OK  ' if ok else 'FAIL'} {j[0]}  {time.time() - t0:.0f}s", flush=True)
        return ok
    with ThreadPoolExecutor(a.workers) as ex:
        res = list(ex.map(work, todo))
    print(f"\ndone {sum(res)}/{len(res)}")
    if not all(res):
        sys.exit(1)


if __name__ == "__main__":
    main()
