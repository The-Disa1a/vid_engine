import subprocess
from tqdm import tqdm
from proglog import ProgressBarLogger
from vid_engine import context

class CleanLogger(ProgressBarLogger):
    def __init__(self, total_frames):
        super().__init__()
        self._pbar = tqdm(total=total_frames, desc="   🎬 Rendering", unit="fr", ncols=80, leave=True)
        self._last = 0
    def bars_callback(self, bar, attr, value, old_value=None):
        if bar == 't' and attr == 'index' and value is not None:
            try:
                delta = int(value) - self._last
                if delta > 0: self._pbar.update(delta); self._last = int(value)
            except: pass
    def close(self):
        try: self._pbar.close()
        except: pass

def check_gpu_real():
    try:
        cmd =['ffmpeg', '-y', '-f', 'lavfi', '-i', 'color=black:s=64x64:d=0.04', '-c:v', 'h264_nvenc', '-f', 'null', '/dev/null']
        return subprocess.run(cmd, capture_output=True, timeout=5).returncode == 0
    except: return False

def init_gpu():
    context.HAS_GPU = check_gpu_real()
    context.VIDEO_CODEC = "h264_nvenc" if context.HAS_GPU else "libx264"
    print(f"[🖥️] Render: {'GPU (NVENC T4) ⚡' if context.HAS_GPU else 'CPU (libx264)'}", flush=True)

def vtt_to_s(t):
    t = t.replace(',','.')
    p = t.split(':')
    if len(p)==3: return float(p[0])*3600+float(p[1])*60+float(p[2])
    if len(p)==2: return float(p[0])*60+float(p[1])
    return float(p[0])

def parse_vtt(f):
    subs, start = [], None
    for line in[l.strip() for l in open(f,'r',encoding='utf-8') if l.strip()]:
        if '-->' in line:
            start, end = line.split('-->')[0].strip(), line.split('-->')[1].strip()
        elif line and not line.startswith('WEBVTT') and start is not None:
            ts, te = vtt_to_s(start), vtt_to_s(end)
            words = line.split()

            if len(words) == 1:
                subs.append({"start": ts, "end": te, "text": words[0].upper()})
            else:
                word_weights =[]
                for w in words:
                    clean_w = ''.join(e for e in w if e.isalnum())
                    weight = len(clean_w) if len(clean_w) > 0 else 1
                    if w.endswith(('.', '!', '?')): weight += 5
                    elif w.endswith((',', ';', ':')): weight += 3
                    word_weights.append(weight)

                total_weight = sum(word_weights)
                ct = ts
                for w, weight in zip(words, word_weights):
                    d = (te - ts) * (weight / total_weight)
                    visual_end = ct + d
                    if w.endswith(('.', '!', '?', ',', ';', ':')): visual_end -= (d * 0.15)
                    subs.append({"start": ct, "end": visual_end, "text": w.upper()})
                    ct += d
            start = None
    return subs

def find_word_timing(keyword, subs):
    kw_words =[ ''.join(e for e in w if e.isalnum()) for w in keyword.upper().split() ]
    kw_words = [w for w in kw_words if w]
    if not kw_words: return 1.0, 2.0

    first_word = kw_words[0]
    for i, s in enumerate(subs):
        s_word = ''.join(e for e in s['text'] if e.isalnum())
        if first_word in s_word or s_word in first_word:
            end_t = s['end']
            if len(kw_words) > 1 and i + len(kw_words) <= len(subs):
                end_idx = i + len(kw_words) - 1
                end_t = subs[end_idx]['end']
            return s['start'], end_t

    if subs:
        mid = len(subs)//2
        return subs[mid]['start'], subs[mid]['start'] + 1.0
    return 1.0, 2.0
