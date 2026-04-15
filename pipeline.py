import os, re, subprocess, traceback, glob, shutil
from datetime import datetime

from vid_engine import context
from vid_engine.llm import get_llm_keywords
from vid_engine.assets import fetch_and_choose_bgm
from vid_engine.templates.default import DefaultTemplate

def build_video_pipeline(target_text, out_name, template=None):
    if template is None:
        template = DefaultTemplate()

    res = (720,1280) if "Portrait" in context.VIDEO_FORMAT else (1280,720)
    print(f"\n[🚀] Booting AI Pipeline for: {out_name}", flush=True)

    raw_text = target_text.replace('**','').replace('###','')
    sentences_list = []
    for match in re.finditer(r'[^.!?]+[.!?]*', raw_text):
        s = match.group().strip()
        if len(s) > 10:
            sentences_list.append(s)

    print(f"   🎬 {len(sentences_list)} scenes (sentences) | {context.VIDEO_FORMAT} | {context.VOICE}", flush=True)

    print("\n[📡] Connecting to Gemini to build Scene Prompts & BGM Mood...", flush=True)
    llm_data = get_llm_keywords(sentences_list)

    if not llm_data or not llm_data[0]:
        print("[❌] Error: Failed to generate Scene Prompts. All LLM models exhausted.", flush=True)
        return False

    llm_kw, bgm_mood = llm_data

    print("[🎧] Securing Global Background Music Track...", flush=True)
    bgm_file = fetch_and_choose_bgm(bgm_mood)

    scene_data =[]
    for i, sentence_text in enumerate(sentences_list):
        try:
            s_file, s_dur = template.make_scene(sentence_text, i, res, kw=llm_kw[i] if llm_kw else None)
            scene_data.append({"file": s_file, "dur": s_dur, "idx": i})
        except Exception as e:
            print(f"[!] Scene {i+1} failed: {e}", flush=True)
            traceback.print_exc()

    OUT = f"{out_name.replace(' ', '_')}.mp4"

    if scene_data:
        print(f"\n[🔥] Rapid Stitching {len(scene_data)} scene(s)...", flush=True)
        with open("list.txt", "w", encoding="utf-8") as f:
            for sd in scene_data: f.write(f"file '{sd['file']}'\n")

        subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", "list.txt", "-c", "copy", "temp_merged.mp4"], check=True, capture_output=True)

        if bgm_file and os.path.exists(bgm_file):
            print(f"   🔊 Underlaying Background Music...", flush=True)
            try:
                subprocess.run([
                    "ffmpeg", "-y",
                    "-i", "temp_merged.mp4",
                    "-stream_loop", "-1", "-i", bgm_file,
                    "-filter_complex", f"[1:a]volume={context.BGM_VOLUME}[bg];[0:a][bg]amix=inputs=2:duration=first:dropout_transition=2:normalize=0[a]",
                    "-map", "0:v:0", "-map", "[a]",
                    "-c:v", "copy", "-c:a", "aac",
                    OUT
                ], check=True, capture_output=True)
            except Exception as e:
                print(f"[⚠️] Complex Audio Underlay failed. Retaining basic merge. {e}", flush=True)
                os.rename("temp_merged.mp4", OUT)
        else:
            print(f"   💬 Wrapping Final Video (No BGM found)...", flush=True)
            subprocess.run([
                "ffmpeg", "-y",
                "-i", "temp_merged.mp4",
                "-c:v", "copy", "-c:a", "copy",
                OUT
            ], check=True, capture_output=True)

        if os.path.exists(OUT):
            context.SUCCESSFUL_VIDEOS.append(OUT)
            print(f"\n[📦] Video '{OUT}' saved and queued for post-process download.", flush=True)

    run_time = datetime.now().strftime("%I-%M-%S_%p")
    archive_dir = f"Session_{run_time}"
    os.makedirs(archive_dir, exist_ok=True)

    print(f"\n[🧹] Archiving workspace files to '{archive_dir}' (Preserving Final Rendered Videos)...", flush=True)
    for ext in["*.mp3","*.vtt","*.mp4","*.webp", "*.txt", "*.jpg", "*.m4a", "*.wav", "*.srt", "*.gif"]:
        for f in glob.glob(ext):
            if f in["Video_and_Music_Sup.txt", "gif_selector.txt", "BGV_selector.txt"]:
                continue
            if f not in context.SUCCESSFUL_VIDEOS:
                try: shutil.move(f, os.path.join(archive_dir, f))
                except Exception as e: pass

    print("✅ Build Cycle Ready!", flush=True)
    return True
