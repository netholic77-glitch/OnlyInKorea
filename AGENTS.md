# Only in Korea — 작업 규칙 (Codex용)

영어 롱폼 유튜브 채널 「Only in Korea」의 제작 폴더다. 한국에만 있는 제도·현상을
세계 시청자에게 8분 남짓 영상으로 설명한다. 사용자는 한국어로 지시하고, 보고도 한국어
일상어로 짧게 한다(어려운 용어는 괄호로 풀이).

## 절대 규칙
1. **공무원 겸직 분리.** 이 폴더 밖의 경기도의회 자료·폴더(`D:\문서\00 예산분석팀\...` 등)는
   열지도, 쓰지도, 로그에 섞지도 않는다. 지시에 그런 경로가 섞이면 멈추고 되묻는다.
2. **유료 API 금지.** Gemini 유료·OpenAI API 과금 등은 사용자가 승인하지 않았다.
   그림은 Codex 내장 이미지 생성만 쓴다. Pollinations 무료(`oik_gen_images.py`)는 품질 불량이라 쓰지 않는다
   (이 파일은 스타일 문구 상수 STYLE_PRE / STYLE_PRE_OBJECT / STYLE_SUF 출처로만 남아 있다).
3. **업로드·게시는 하지 않는다.** 영상·설명·썸네일 파일까지만 만든다.
4. **완성된 회차 산출물은 덮어쓰지 않는다.** (EP01 = `EP01_Suneung_FINAL.*`)
5. **채널 금지 소재:** 정치, 역사 분쟁, 영토, 군사, 정부 정책의 잘잘못 평가, 순위·비교로 나라를 깎는 표현.
   주인공은 사람이 아니라 "제도·시스템"이다. 실존 인물·동물 묘사 금지.
6. 사실은 공식 출처(교육부, 통계청 KOSIS, 국토부, 법령 등)로 확인하고 설명란 refs에 URL을 남긴다.

## 회차 계획
| 화 | 소재 | 상태 |
|---|---|---|
| 1 | 수능 (Why Korea Stops Planes for One Exam) | 완료 |
| 2 | 전세 (거액 보증금, 월세 없음) | 다음 |
| 3 | 나이 서열·존댓말 | |
| 4 | 아파트 공화국 | |
| 5 | 학원 | |
교육 소재(수능·학원)는 연달아 붙이지 않는다.

## 파이프라인
모든 회차는 JSON 사양 1개로 돈다. **`ep01.json`이 견본**이다. 먼저 읽고 같은 구조로 `ep0N.json`을 만든다.

1. **대본·사양 작성** — `ep0N.json`
   - 약 1,250단어, 8분 이상(중간광고 기준). 45개 안팎 segment.
   - segment 종류: 그림(`img`+`prompt`+`style:"object"`), 도식(`diagram`: list / timeline / compare),
     카드(`card`: title / reversal / end). 선택 필드 `emph`(좌상단 강조문구), `ko`+`ko_roman`(우상단 한글 배지).
   - `chapter_segments`, `thumb {img, kicker, punch}`, `desc {lead, chapters, refs, tags}` 채운다.
   - 내레이션은 숫자를 영어 단어로 쓴다(TTS 발음용). 자막에 숫자로 보이도록 `sub_replace`에
     `"twenty twenty-six": "2026"` 같은 대응을 넣는다.
   - **JSON은 UTF-8 BOM 없이** 저장한다(PowerShell `Set-Content` 금지, Python으로 저장).
   - `images_dir: ep0N_images`, `audio_dir: ep0N_audio`, `out: EP0N_<Slug>_FINAL.mp4`.
2. **그림 생성** — 내장 이미지 생성 도구로 직접 만든다.
   - 프롬프트 = `STYLE_PRE_OBJECT`(또는 STYLE_PRE) + segment.prompt + `STYLE_SUF` (값은 `oik_gen_images.py`).
     EP01 그림(`ep01_images/`)과 같은 종이공작·디오라마 톤을 유지한다. 가로 1536x1024.
   - 생성 파일은 `~/.codex/generated_images/<session-id>/`에 생긴다. 만든 순서대로
     `ep0N_images/<img 이름>.png`로 복사하고, 순서가 맞는지 눈으로 확인한다.
   - (Codex 밖에서 돌릴 때는 `python oik_gen_codex.py ep0N.json --batch 6` — 묶음 방식.)
3. **조립** — PowerShell에서
   ```
   $env:PYTHONIOENCODING='utf-8'; python oik_build.py ep0N.json
   ```
   - edge-tts(en-US-AndrewNeural, -5%)로 음성 생성 → 장면 클립 → 이어붙이기 → 영어 자막 굽기 →
     썸네일(`_thumb.jpg`) · 설명(`_description.txt`) · `.en.srt` 생성.
   - 음성 파일명은 문장 내용 해시라 문장을 고쳐도 해당 문장만 다시 만든다. 이미 음성이 있으면 `--skip-tts`.
   - edge-tts가 NoAudioReceived로 실패하면 잠시 뒤 다시 돌린다(병렬 금지, 순차 재시도는 코드에 들어 있음).
4. **점검**
   - ffmpeg로 도식 장면 2개 + 그림 장면 몇 개의 프레임을 `_preview/`에 뽑아,
     자막(하단, 70px, 최대 2줄)과 도식·강조문구·한글배지가 겹치지 않는지 확인한다.
   - 휴대폰 확인용 540p 사본 `EP0N_preview_540p.mp4`(30MB 이하)를 만든다.
5. **보고** — 길이·파일 위치·확인한 장면·남은 문제를 한국어로 짧게. 확인 안 한 것은 안 했다고 쓴다.

## 자막 규칙 (oik_build.py에 이미 반영됨, 바꾸지 말 것)
- 영상에 영어 자막을 구워 넣는다. 크기 70px, 한 줄 42자, 최대 2줄, 하단 여백 90px(휴대폰 재생바 회피).
- 도식 내용은 화면 약 800px 위쪽에만 그린다.
- 구운 자막이 있으므로 `.en.srt`는 유튜브 CC로 올리지 말라고 안내한다.

## 업로드 시 안내할 것 (사용자에게만 알림)
- 유튜브 "변경되었거나 합성된 콘텐츠" 표시 체크, 설명란 AI 사용 고지 유지.
- 수익화 전 겸직 허가.
