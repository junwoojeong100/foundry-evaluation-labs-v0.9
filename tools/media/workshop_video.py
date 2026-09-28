#!/usr/bin/env python3
"""Record real CLI output locally and edit captured browser videos."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import time
from datetime import datetime
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[2]
PRIVATE = ROOT / "results" / "media"
WORK = PRIVATE / "work"
RAW = PRIVATE / "raw"
OUTPUT = ROOT / "docs" / "media"
FONT = Path("/System/Library/Fonts/AppleSDGothicNeo.ttc")
SCENES = [
    {
        "id": "01-resources", "kind": "portal", "seconds": 18,
        "en": ["Verify the retained Azure resources", "Sweden Central resources and evaluation calls work. A separate organization-policy diagnostic deployment needs administrator follow-up. Keep all resources."],
        "ko": ["보존한 Azure 리소스 확인", "Sweden Central 리소스와 평가 호출은 동작합니다. 별도 조직 진단 정책의 배포 실패는 관리자 확인 대상입니다. 리소스는 모두 보존합니다."],
    },
    {
        "id": "02-setup", "kind": "terminal", "seconds": 22,
        "en": ["Check the live CLI connection", "These are actual Azure CLI and doctor commands. The account was checked off-camera; personal identifiers are redacted."],
        "ko": ["CLI로 실제 연결 확인", "실제 Azure CLI와 doctor 명령을 실행합니다. 계정은 녹화 전에 대조했으며 개인 식별 정보는 가렸습니다."],
        "commands": [
            'az group show --name "$LAB_RG" --subscription "$LAB_SUB" --query "{location:location,state:properties.provisioningState}" -o json',
            "python lab.py doctor --live",
        ],
    },
    {
        "id": "03-model", "kind": "portal", "seconds": 18,
        "en": ["A model name is not a deployment name", "The existing eval-model deployment uses gpt-6-luna. Generation and judging use the same deployment; no resource is recreated."],
        "ko": ["모델명과 배포 이름은 다릅니다", "기존 eval-model 배포는 gpt-6-luna를 사용합니다. 생성·채점에 같은 배포를 쓰며 리소스를 다시 만들지 않습니다."],
    },
    {
        "id": "04-smoke", "kind": "terminal", "seconds": 28,
        "en": ["Run one fresh smoke evaluation", "This recording makes one new paid model call and evaluates that saved answer. Wait for both scores and reasons, not only remote Completed."],
        "ko": ["새 답변 한 건으로 생성·평가", "이 장면은 실제 유료 모델 호출 한 건과 저장된 답변의 평가를 새로 실행합니다. Completed뿐 아니라 두 점수·이유 저장까지 확인합니다."],
        "commands": [
            "python lab.py run --mode live --prompt v1 --data data/my-case.example.jsonl --out results/video-smoke",
            "python lab.py judge results/video-smoke --wait-seconds 120",
        ],
    },
    {
        "id": "05-baseline", "kind": "terminal", "seconds": 22,
        "en": ["Inspect retained LIVE baseline evidence", "The completed dev run is reused, not regenerated. D04 correctly avoids inventing an overseas limit; the generic judge still gives Relevance 3."],
        "ko": ["보존된 LIVE 기준 실행 읽기", "완료된 dev 결과를 재사용하며 새로 생성하지 않습니다. D04는 해외 한도를 추측하지 않았지만 일반 Relevance 점수는 3입니다."],
        "commands": [
            "python lab.py run --mode live --prompt v1 --out results/baseline",
            "python lab.py inspect results/baseline D04",
        ],
    },
    {
        "id": "06-evaluation", "kind": "portal", "seconds": 22,
        "en": ["Match the same answer in Foundry", "Find D04 by its question or ID. Portal Pass at 3 differs from this workshop's threshold of 4. Read the original answer and the judge's reason."],
        "ko": ["Foundry에서 같은 답변 대조", "질문이나 ID로 D04를 찾습니다. 포털의 3점 Pass와 실습의 4점 합격선은 다릅니다. 답변 원문과 채점 이유를 함께 읽습니다."],
    },
    {
        "id": "07-compare", "kind": "terminal", "seconds": 22,
        "en": ["A better business score can hide a regression", "These are the retained LIVE runs. Business checks improve from 87.5% to 100%, but D08 Relevance regresses. Do not tune thresholds after seeing scores."],
        "ko": ["업무 점수가 올라도 회귀를 확인", "보존된 LIVE 실행의 업무 통과율은 87.5%에서 100%로 올랐지만 D08 Relevance는 회귀했습니다. 결과를 보고 합격선을 낮추지 않습니다."],
        "commands": [
            "python lab.py compare results/baseline results/candidate",
            "python lab.py inspect results/candidate D08",
        ],
    },
    {
        "id": "08-portal-compare", "kind": "portal", "seconds": 18,
        "en": ["Compare only the two dev runs", "Use V1 as Baseline. Do not mix holdout into before/after comparison. Too few samples is not evidence of a statistically established improvement."],
        "ko": ["같은 dev 두 실행만 비교", "V1을 Baseline으로 지정합니다. Holdout을 전후 비교에 섞지 않습니다. Too few samples는 통계적 개선이 입증됐다는 뜻이 아닙니다."],
    },
    {
        "id": "09-gate", "kind": "terminal", "seconds": 26,
        "en": ["Freeze the candidate, then respect BLOCK", "The saved holdout uses the frozen candidate. The gate blocks on Relevance failures and missing actual human review. AI-assisted reviews are not human approval."],
        "ko": ["후보를 고정하고 BLOCK을 존중", "저장된 holdout은 고정 후보로 실행한 결과입니다. Relevance 실패와 실제 사람 검토 미완료로 차단됩니다. AI 보조 검토는 사람 승인이 아닙니다."],
        "commands": [
            "python lab.py run --mode live --frozen results/candidate --split holdout --out results/holdout",
            "python lab.py gate results/baseline results/candidate results/holdout",
        ],
    },
    {
        "id": "10-extra", "kind": "terminal", "seconds": 20,
        "en": ["Validate an extra case and retain the evidence", "N02 tests the travel date, not the claim date. Its saved LIVE answer passes. Keep the reports and Azure resources; a small workshop is not release approval."],
        "ko": ["추가 사례 확인과 증거 보존", "N02는 정산일이 아닌 출장일 적용을 검사하며 저장된 LIVE 답변은 통과했습니다. 보고서와 Azure 리소스를 보존합니다. 작은 실습은 출시 승인이 아닙니다."],
        "commands": [
            "python lab.py validate-data data/my-case.jsonl",
            "python lab.py inspect results/my-case N02",
        ],
    },
]


def load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def scene_for(name: str, scenes=SCENES) -> dict:
    return next(scene for scene in scenes if scene["id"] == name)


def project_context() -> dict:
    identity = load(ROOT / "results" / "azure-identity.json")
    current = json.loads(subprocess.check_output(
        ["az", "account", "show", "--output", "json"], text=True,
    ))
    if current["id"] != identity["subscriptionId"] or current["user"]["name"].casefold() != identity["account"].casefold():
        raise RuntimeError("The current Azure identity differs from the verified workshop identity.")
    group = load(ROOT / "results" / "azure-resource-group.json")
    account = load(ROOT / "results" / "azure-foundry-account.json")
    baseline = load(ROOT / "results" / "baseline" / "judge.json")
    prefix = baseline["report_url"].split("/build/")[0]
    display_name = subprocess.check_output(
        ["az", "ad", "signed-in-user", "show", "--query", "displayName", "-o", "tsv"],
        text=True,
    ).strip()
    return {
        "subscription": identity["subscriptionId"], "tenant": identity["tenantId"],
        "group": group["name"], "account": account["name"],
        "redact": [
            identity["account"], identity["subscriptionId"], identity["tenantId"],
            display_name, current["name"], identity["account"].split("@")[-1].upper(),
        ],
        "urls": {
            "01-resources": f"https://portal.azure.com/#@{identity['tenantId']}/resource{group['id']}/overview",
            "03-model": prefix + "/build/models/deployments?tid=" + identity["tenantId"],
            "06-evaluation": baseline["report_url"] + "?tid=" + identity["tenantId"],
        },
    }


def redact(text: str, values: list[str]) -> str:
    text = text.replace(str(ROOT), ".")
    for value in sorted((value for value in values if value), key=len, reverse=True):
        text = re.sub(re.escape(value), "[redacted]", text, flags=re.IGNORECASE)
    text = re.sub(r"https://ai\.azure\.com/\S+", "[Foundry report URL saved locally]", text)
    text = re.sub(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b", "[account redacted]", text)
    return re.sub(r"\b[0-9a-fA-F]{8}(?:-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}\b", "[ID redacted]", text)


def prepare(name: str, *, scenes=SCENES, private=PRIVATE, context=None, comparison_url: str | None = None) -> None:
    scene = scene_for(name, scenes)
    if comparison_url is not None:
        url = urlsplit(comparison_url)
        if (
            name != "08-portal-compare" or url.scheme != "https"
            or url.netloc.casefold() != "ai.azure.com" or re.search(r"\s", comparison_url)
            or "/compare/" not in url.path or not url.path.split("/compare/", 1)[1].strip("/")
        ):
            raise ValueError("--comparison-url must be a verified Foundry Compare runs URL for 08-portal-compare.")
    if name == "08-portal-compare" and comparison_url is None and (
        context is None or not context["urls"].get(name)
    ):
        raise ValueError("Supply the verified Foundry Compare runs URL with --comparison-url.")
    context = project_context() if context is None else context
    if comparison_url is not None:
        context = {**context, "urls": {**context["urls"], name: comparison_url}}
    work, raw = private / "work", private / "raw"
    server = load(work / "server.json")
    config = {
        "id": name, "kind": scene["kind"], "title": scene["en"][0],
        "directory": str(raw / name), "redact": context["redact"],
        "url": context["urls"].get(name, server["url"] + "/terminal.html"),
    }
    if (raw / name).exists() and list((raw / name).glob("*.webm")):
        raise RuntimeError(f"Capture already exists for {name}; do not overwrite it.")
    save(work / "capture-config.json", config)
    save(work / "terminal.json", {
        "title": scene["en"][0], "label": scene.get("label", "One fresh smoke call" if name == "04-smoke" else "Retained LIVE evidence · no regeneration"),
        "lines": [], "status": "Ready to record actual commands",
    })
    save(private / "context.json", context)
    print(f"Prepared {name} ({scene['kind']})")


def run_scene(name: str, *, scenes=SCENES, private=PRIVATE) -> None:
    scene = scene_for(name, scenes)
    if scene["kind"] != "terminal":
        raise ValueError("Only terminal scenes have CLI commands.")
    work = private / "work"
    context = load(private / "context.json")
    state = load(work / "terminal.json")
    env = dict(os.environ)
    env.update({
        "PATH": str(ROOT / ".venv" / "bin") + os.pathsep + env["PATH"],
        "PYTHONUNBUFFERED": "1", "LAB_RG": context["group"], "LAB_SUB": context["subscription"],
        "COLUMNS": "104", "TERM": "xterm-256color", "NO_COLOR": "1",
    })
    if "search" in context:
        env["LAB_SEARCH"] = context["search"]
    events = []
    for command in scene["commands"]:
        state["lines"].append({"kind": "command", "text": "$ " + command})
        state["status"] = "Executing a real CLI command"
        save(work / "terminal.json", state)
        started = time.time()
        events.append({"command": command, "started_at_ms": round(started * 1000)})
        time.sleep(2)
        process = subprocess.Popen(
            ["/bin/bash", "--noprofile", "--norc", "-c", command],
            cwd=ROOT, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, encoding="utf-8",
        )
        output = []
        for line in process.stdout:
            output.append(line)
            visible = redact(line.rstrip(), context["redact"])
            state["lines"].append({"kind": "output", "text": visible})
            save(work / "terminal.json", state)
        code = process.wait()
        expected = 2 if command.startswith("python lab.py gate ") else 0
        events[-1].update({
            "finished_at_ms": round(time.time() * 1000), "exit_code": code,
            "expected_exit_code": expected,
            "stdout_sha256": hashlib.sha256("".join(output).encode()).hexdigest(),
        })
        save(private / f"{name}.commands.json", events)
        if code != expected:
            state["status"] = f"Execution error: exit {code}; expected {expected}"
            save(work / "terminal.json", state)
            raise RuntimeError(f"{command}: exit {code}; original output is preserved in the local recording.")
        state["lines"].append({"kind": "status", "text": f"Exit {code}" + (" · intentional quality BLOCK" if code == 2 else " · command completed")})
        state["status"] = "BLOCK is a quality decision, not an execution error" if code == 2 else "Evidence saved; no scores were altered"
        save(work / "terminal.json", state)
        time.sleep(7)
    print(f"Recorded {len(events)} real commands for {name}")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, private=PRIVATE, scenes=SCENES, **kwargs):
        self.private = private
        self.scenes = scenes
        super().__init__(*args, directory=str(private / "work"), **kwargs)

    def log_message(self, *_args):
        pass

    def do_POST(self):
        if self.path != "/recording":
            self.send_error(404)
            return
        size = int(self.headers.get("Content-Length", "0"))
        if not 0 < size < 16384:
            self.send_error(400)
            return
        data = json.loads(self.rfile.read(size))
        scene_for(data["id"], self.scenes)
        if not Path(data["path"]).resolve().is_relative_to((self.private / "raw").resolve()):
            self.send_error(400)
            return
        save(self.private / f"{data['id']}.recording.json", data)
        self.send_response(204)
        self.end_headers()


def serve(*, scenes=SCENES, private=PRIVATE) -> None:
    work = private / "work"
    work.mkdir(parents=True, exist_ok=True)
    template = Path(__file__).with_name("terminal.html")
    (work / "terminal.html").write_bytes(template.read_bytes())
    server = ThreadingHTTPServer(("127.0.0.1", 0), partial(Handler, private=private, scenes=scenes))
    url = f"http://127.0.0.1:{server.server_port}"
    save(work / "server.json", {"url": url})
    print(f"Recording server: {url}", flush=True)
    server.serve_forever()


def probe(path: Path) -> dict:
    return json.loads(subprocess.check_output([
        "ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(path),
    ], text=True))


def wrapped(draw, text: str, font, width: int) -> list[str]:
    lines, line = [], ""
    for word in text.split():
        candidate = f"{line} {word}".strip()
        if line and draw.textlength(candidate, font=font) > width:
            lines.append(line)
            line = ""
        for character in word:
            if draw.textlength(line + character, font=font) > width:
                lines.append(line.strip())
                line = ""
            line += character
        line += " "
    if line:
        lines.append(line.strip())
    return lines


def overlay(path: Path, language: str, scene: dict, index: int, *, total_scenes=len(SCENES)) -> None:
    from PIL import Image, ImageDraw, ImageFont
    image = Image.new("RGBA", (1920, 1080))
    draw = ImageDraw.Draw(image)
    title_font = ImageFont.truetype(str(FONT), 38)
    caption_font = ImageFont.truetype(str(FONT), 38)
    small = ImageFont.truetype(str(FONT), 23)
    draw.rectangle((0, 0, 1920, 78), fill=(10, 18, 32, 255))
    draw.rounded_rectangle((28, 16, 105, 64), radius=10, fill=(28, 103, 202, 255))
    draw.text((46, 19), f"{index:02}", font=title_font, fill="white")
    draw.text((128, 18), scene[language][0], font=title_font, fill="white")
    draw.rectangle((0, 888, 1920, 1080), fill=(10, 18, 32, 255))
    lines = wrapped(draw, scene[language][1], caption_font, 1780)
    if len(lines) > 3:
        raise ValueError(f"Caption too long: {scene['id']} {language}")
    for row, line in enumerate(lines):
        draw.text((64, 908 + row * 47), line, font=caption_font, fill=(243, 247, 255))
    note = "Actual screen recording · identifiers redacted" if language == "en" else "실제 화면 녹화 · 식별 정보 가림"
    draw.text((64, 1045), note, font=small, fill=(146, 171, 199))
    draw.rectangle((0, 1074, int(1920 * index / total_scenes), 1079), fill=(59, 159, 255))
    image.save(path)


def card(path: Path, language: str, closing: bool = False, *, topic="core") -> None:
    from PIL import Image, ImageDraw, ImageFont
    image = Image.new("RGB", (1920, 1080), (9, 17, 32))
    draw = ImageDraw.Draw(image)
    title = ImageFont.truetype(str(FONT), 82)
    body = ImageFont.truetype(str(FONT), 42)
    small = ImageFont.truetype(str(FONT), 30)
    draw.rectangle((104, 145, 114, 820), fill=(58, 154, 249))
    if topic == "success":
        if closing:
            heading = "Fresh questions.\nVerified acceptance." if language == "en" else "새 질문에서도\n실습 기준 합격"
            sub = "Lab acceptance passed. Human production approval is separate." if language == "en" else "실습 기준은 합격했습니다. 사람의 운영 승인은 별도입니다."
        else:
            heading = "From a real failure\nto verified improvement." if language == "en" else "실제 실패에서\n검증된 개선까지"
            sub = "One Search service · vectors · LLM planning · calibrated evaluation" if language == "en" else "검색 서비스 하나 · 벡터 · LLM 계획 · 교정된 평가"
    elif topic == "rag":
        if closing:
            heading = "Retrieval is not\nanswer quality." if language == "en" else "검색 품질과\n답변 품질은 다릅니다."
            sub = "REVIEW_REQUIRED · keep the original evidence." if language == "en" else "REVIEW_REQUIRED · 원본 근거를 보존합니다."
        else:
            heading = "Retrieve first.\nThen evaluate." if language == "en" else "실제로 검색하고\n답변을 평가합니다."
            sub = "Optional RAG · Azure AI Search + Foundry IQ" if language == "en" else "선택형 RAG · Azure AI Search + Foundry IQ"
    elif closing:
        heading = "Keep the evidence.\nRespect the gate." if language == "en" else "증거를 보존하고\n판정을 존중합니다."
        sub = "BLOCK is a valid outcome. Human approval is still required." if language == "en" else "BLOCK도 유효한 결과입니다. 실제 사람 검토는 별도로 필요합니다."
    else:
        heading = "Can you trust\nan AI answer?" if language == "en" else "AI 답변,\n믿어도 될까요?"
        sub = "Microsoft Foundry Evaluation · recorded walkthrough" if language == "en" else "Microsoft Foundry Evaluation · 실제 화면 요약"
    draw.multiline_text((158, 210), heading, font=title, fill="white", spacing=22)
    for row, line in enumerate(wrapped(draw, sub, body, 1590)):
        draw.text((160, 525 + row * 60), line, font=body, fill=(181, 211, 243))
    draw.text((160, 715), "gpt-6-luna  /  swedencentral  /  eval-model", font=body, fill=(93, 185, 255))
    if topic == "success":
        note = "Every final answer must pass all required metrics, including Relevance. No scores are altered." if language == "en" else "최종 응답은 Relevance를 포함한 모든 필수 지표를 통과해야 합니다. 점수는 조작하지 않습니다."
    elif topic == "rag":
        note = "Live retrieval + retained RAG evaluations. GA extractive retrieval, not LLM query planning." if language == "en" else "실제 검색 + 보존된 RAG 평가. 정식 추출형 검색이며 LLM 쿼리 계획은 사용하지 않습니다."
    else:
        note = "One fresh smoke check + retained LIVE evidence. Captions only; no narration." if language == "en" else "새 연결 확인 1건 + 보존된 LIVE 증거. 자막 영상이며 음성 해설은 없습니다."
    for row, line in enumerate(wrapped(draw, note, small, 1570)):
        draw.text((160, 830 + row * 43), line, font=small, fill=(165, 185, 209))
    image.save(path)


def stamp(seconds: float) -> str:
    milliseconds = round(seconds * 1000)
    hours, milliseconds = divmod(milliseconds, 3600000)
    minutes, milliseconds = divmod(milliseconds, 60000)
    whole, milliseconds = divmod(milliseconds, 1000)
    return f"{hours:02}:{minutes:02}:{whole:02},{milliseconds:03}"


def ffmpeg(arguments: list[str]) -> None:
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *arguments], check=True)


def render(*, scenes=SCENES, private=PRIVATE, output=OUTPUT, prefix="workshop-summary", topic="core", recorded_on="2026-09-27") -> None:
    output.mkdir(parents=True, exist_ok=True)
    edited = private / "edited"
    edited.mkdir(parents=True, exist_ok=True)
    encoding = ["-an", "-map_metadata", "-1", "-c:v", "libx264", "-threads", "2", "-preset", "medium", "-crf", "22", "-pix_fmt", "yuv420p", "-r", "24"]
    if recorded_on is None:
        started = min(load(private / f"{scene['id']}.recording.json")["started_at_ms"] for scene in scenes)
        recorded_on = datetime.fromtimestamp(started / 1000).astimezone().date().isoformat()
    manifest = {"recorded_on": recorded_on, "source": "Actual headless Playwright screen recordings and real CLI execution", "videos": {}}
    for language in ("en", "ko"):
        parts, subtitles, chapters = [], [], []
        elapsed = 0.0
        png = edited / f"intro-{language}.png"
        segment = edited / f"intro-{language}.mp4"
        card(png, language, topic=topic)
        ffmpeg(["-loop", "1", "-i", str(png), "-t", "7", *encoding, str(segment)])
        parts.append(segment)
        elapsed += 7
        for index, scene in enumerate(scenes, 1):
            record = load(private / f"{scene['id']}.recording.json")
            raw = Path(record["path"])
            duration = float(probe(raw)["format"]["duration"])
            start = max(0, record["ready_offset_ms"] / 1000 - 0.3)
            end = duration - 0.2
            if "action_end_offset_ms" in record:
                end = min(end, record["action_end_offset_ms"] / 1000 + 0.4)
            command_log = private / f"{scene['id']}.commands.json"
            if command_log.exists():
                commands = load(command_log)
                start = max(start, (commands[0]["started_at_ms"] - record["started_at_ms"]) / 1000 - 1)
                end = min(end, (commands[-1]["finished_at_ms"] - record["started_at_ms"]) / 1000 + 5)
            usable = end - start
            if usable < 3:
                raise ValueError(f"Insufficient actual footage: {scene['id']}, {usable:.2f}s")
            target = scene["seconds"]
            factor = target / usable
            png = edited / f"{scene['id']}.{language}.png"
            segment = edited / f"{scene['id']}.{language}.mp4"
            overlay(png, language, scene, index, total_scenes=len(scenes))
            ffmpeg([
                "-ss", f"{start:.3f}", "-t", f"{usable:.3f}", "-i", str(raw),
                "-loop", "1", "-i", str(png),
                "-filter_complex", f"[0:v]setpts={factor:.8f}*(PTS-STARTPTS),scale=1920:1080,setsar=1,fps=24[base];[base][1:v]overlay=0:0:shortest=1",
                "-t", str(target), *encoding, str(segment),
            ])
            parts.append(segment)
            subtitles.append(f"{index}\n{stamp(elapsed)} --> {stamp(elapsed + target)}\n{scene[language][0]}\n{scene[language][1]}\n")
            chapters.append({"start": elapsed, "duration": target, "title": scene[language][0], "scene": scene["id"]})
            elapsed += target
        png = edited / f"outro-{language}.png"
        segment = edited / f"outro-{language}.mp4"
        card(png, language, True, topic=topic)
        ffmpeg(["-loop", "1", "-i", str(png), "-t", "7", *encoding, str(segment)])
        parts.append(segment)
        elapsed += 7
        listing = edited / f"concat-{language}.txt"
        listing.write_text("".join(f"file '{part.as_posix()}'\n" for part in parts), encoding="utf-8")
        destination = output / f"{prefix}.{language}.mp4"
        ffmpeg(["-f", "concat", "-safe", "0", "-i", str(listing), "-map_metadata", "-1", "-c", "copy", "-movflags", "+faststart", str(destination)])
        (output / f"{prefix}.{language}.srt").write_text("\n".join(subtitles), encoding="utf-8")
        card(output / f"{prefix}.{language}.png", language, topic=topic)
        manifest["videos"][language] = {
            "file": destination.name, "duration_seconds": elapsed, "chapters": chapters,
            "bytes": destination.stat().st_size,
            "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
            "audio": "none; localized burned-in captions and separate SRT",
        }
        print(f"Rendered {destination.name}: {elapsed:.0f}s", flush=True)
    save(output / "manifest.json", manifest)


def verify(*, output=OUTPUT, scene_count=len(SCENES), prefix="workshop-summary", expected_marker="BLOCK") -> None:
    manifest = load(output / "manifest.json")
    for language, item in manifest["videos"].items():
        path = output / item["file"]
        media = probe(path)
        stream = next(stream for stream in media["streams"] if stream["codec_type"] == "video")
        assert stream["codec_name"] == "h264"
        assert (stream["width"], stream["height"]) == (1920, 1080)
        assert stream["pix_fmt"] == "yuv420p"
        assert abs(float(media["format"]["duration"]) - item["duration_seconds"]) < 1
        assert path.stat().st_size < 50 * 1024 * 1024
        assert hashlib.sha256(path.read_bytes()).hexdigest() == item["sha256"]
        assert len(item["chapters"]) == scene_count
        subtitle = (output / f"{prefix}.{language}.srt").read_text(encoding="utf-8")
        assert subtitle.count(" --> ") == scene_count
        assert expected_marker in subtitle
        ffmpeg(["-i", str(path), "-f", "null", "-"])
        print(f"Verified {language}: H.264 1080p, {float(media['format']['duration']):.1f}s, full decode OK")


def main() -> None:
    os.umask(0o077)
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("serve", "prepare", "run", "render", "verify"))
    parser.add_argument("scene", nargs="?")
    parser.add_argument("--comparison-url", help="Verified Foundry Compare runs URL for prepare 08-portal-compare.")
    args = parser.parse_args()
    if args.comparison_url is not None and (args.action != "prepare" or args.scene != "08-portal-compare"):
        parser.error("--comparison-url is only valid for prepare 08-portal-compare.")
    if args.action in ("prepare", "run"):
        if not args.scene:
            parser.error("A scene ID is required.")
        if args.action == "prepare":
            prepare(args.scene, comparison_url=args.comparison_url)
        else:
            run_scene(args.scene)
    else:
        {"serve": serve, "render": render, "verify": verify}[args.action]()


if __name__ == "__main__":
    main()
