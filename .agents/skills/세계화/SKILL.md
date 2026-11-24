---
name: 세계화
description: >
  영어 유튜브 해설 채널 「Only in Korea」(@...)의 한 편을 기획부터 영상 완성까지 만들어내는 제작 파이프라인이다.
  한국에만 있는 고유한 제도와 사회 구조(수능날, 전세, 나이 서열·존댓말, 아파트 공화국, 학원 등)를 8분 이상(약 1,250단어)
  롱폼 영상으로 세계 시청자에게 차분하고 객관적으로 설명한다.
  "세계화", "세계화 스킬", "Only in Korea", "OnlyInKorea", "온리인코리아", "영어 영상 만들어줘" 같은 지시에서 발동한다.
  ①공식 출처 사실 확인(국토부, KOSIS, 법령, HUG 등) ②반전 오프닝 및 영문 대본 작성(약 1,250단어, 8분 이상, 시스템 중심 객관적 설명, 정책/인물 평가 배제, 대칭적 비용/리스크 섹션 필수)
  ③ep0N.json 사양서 작성(UTF-8 BOM 없음, sub_replace 숫자 표기 매핑) ④종이공작 톤 내장 이미지 생성 ⑤oik_build.py 영상 조립(edge-tts, 다이어그램, 70px 자막 번인)
  ⑥자막 겹침 검증 및 540p 모바일 미리보기본 제작까지 일관되게 수행한다.
  경기도의회 업무와 무관한 개인 채널 작업이며, 공무원 겸직 분리 가드레일을 매 편 강제한다.
license: MIT
metadata:
  category: content-production
  locale: en-US
  project_dir: '%USERPROFILE%/Desktop/OnlyInKorea'
  requires: Python(edge_tts, mutagen, imageio_ffmpeg, Pillow)
---

# Only in Korea (세계화) — 영어 롱폼 해설 영상 제작 파이프라인

한국에만 있는 제도·사회 구조 하나를 다루어 **세계 시청자를 위한 8분 이상 롱폼 영상(1920x1080 mp4 + 설명문 + 썸네일 + 540p 미리보기본)**까지 완결한다.

- 프로젝트 폴더: `%USERPROFILE%\Desktop\OnlyInKorea` (`C:\Users\Usery\Desktop\OnlyInKorea`)
- 회차별 산출물: `epNN.json`, `epNN_images/`, `epNN_audio/`, `EP0N_<Slug>_FINAL.mp4`, `EP0N_<Slug>_FINAL_thumb.jpg`, `EP0N_<Slug>_FINAL_description.txt`, `EP0N_<Slug>_FINAL.en.srt`, `EP0N_preview_540p.mp4`

---

## ⛔ 절대 규칙 — 작업 전 확인

1. **공무원 겸직 분리.**
   - 이 폴더 밖의 경기도의회 자료·폴더(`D:\문서\00 예산분석팀\...` 등)는 열지도, 쓰지도, 로그에 섞지도 않는다.
   - 지시에 그런 경로가 섞이면 즉시 멈추고 되묻는다.
2. **유료 API 사용 금지.**
   - Gemini 유료·OpenAI API 과금 등은 사용자가 승인하지 않았다.
   - 그림은 내장 이미지 생성만 사용한다. Pollinations 무료(`oik_gen_images.py`)는 품질 불량으로 사용 금지.
3. **업로드·게시는 하지 않는다.**
   - 로컬 파일(영상, 설명문, 썸네일, 자막)까지만 제작한다.
4. **기존 완성 회차 덮어쓰기 금지.**
   - 이미 완성된 회차 파일(예: `EP01_Suneung_FINAL.*`)은 절대 건드리지 않는다.
5. **채널 금지 소재:**
   - 정치, 역사 분쟁, 영토, 군사, 정부 정책의 잘잘못 평가, 순위·비교로 나라를 깎거나 치켜세우는 표현 금지.
   - 문장의 주인공은 사람이 아니라 언제나 **"제도·시스템(The System / Design)"**이다.
   - "Koreans are..." 식의 국민성 일반화 금지. 실존 인물·동물 묘사 금지.
6. **대칭적 비용(Cost & Trade-off) 섹션 필수.**
   - 제도의 작동 원리만 말하면 홍보물처럼 보여 반발을 부른다.
   - 제도에 수반되는 기회비용, 자금 묶임, 이자 손실, 반환 리스크 등의 비용 섹션을 반드시 대본에 포함한다.
7. **공식 1차 출처 확인.**
   - 국토교통부, 교육부, 통계청 KOSIS, 국가법령정보센터, 주택도시보증공사(HUG), 서울특별시 등 공공 출처로 교차 확인하고 설명란 `refs`에 URL을 남긴다.

---

## 📅 회차 계획 (순서 유지)

| 화 | 슬러그 | 소재 | 핵심 훅 (영문) | 상태 |
|---|---|---|---|---|
| 1 | suneung | 수능 | Why Korea Stops Planes for One Exam | 완료 |
| 2 | jeonse | 전세 | Pay a Fortune. Pay No Rent. Get It All Back. | 완료 |
| 3 | age | 나이 서열·존댓말 | The Strict Rules of Korean Age & Respect | 예정 |
| 4 | apt | 아파트 공화국 | Why Most Koreans Live in Identical Towers | 예정 |
| 5 | hagwon | 학원 | The Secret Education Machine Running Till 10 PM | 예정 |

> ⚠️ 교육 소재(수능·학원)는 연달아 붙이지 않는다.

---

## 🛠️ 제작 파이프라인 (6단계)

### 1단계: 사실 확인 및 영문 대본 작성
- **분량:** 약 1,250단어, 8분 이상 (중간광고 삽입 가능 기준), 40~45개 안팎의 세그먼트.
- **도입부 훅:** 영어권 시청자가 직관적으로 놀랄 만한 반전(예: 월세가 0원인데 거액을 맡기고 나갈 때 전액 돌려받음)을 맨 앞에 배치.
- **톤앤매너:** 담담하고 객관적인 시스템 해설. 우열 비교나 정책 비판 배제.
- **TTS 및 자막 대응:**
  - 내레이션 텍스트(`text`)는 음성 합성(TTS)이 자연스럽게 읽도록 숫자를 영단어로 표기(예: `two hundred million won`, `twenty twenty-six`).
  - 자막에 숫자로 표시되도록 `sub_replace` 매핑 테이블을 작성(예: `"two hundred million won": "₩200,000,000"`).

### 2단계: 사양서 JSON 작성 (`ep0N.json`)
`ep01.json` 구조를 그대로 준수하여 작성한다.
- **반드시 UTF-8 BOM 없이 저장** (PowerShell `Set-Content` 대신 Python 등으로 저장).
- 주요 필드:
  - `episode`, `slug`, `title`, `voice` (`en-US-AndrewNeural`), `rate` (`-5%` 또는 적정 속도)
  - `images_dir: "ep0N_images"`, `audio_dir: "ep0N_audio"`, `out: "EP0N_<Slug>_FINAL.mp4"`
  - `segments`: `img`(+`prompt`+`style:"object"`), `diagram`(`list`/`timeline`/`compare`), `card`(`title`/`reversal`/`end`), `emph`(강조 자막), `ko`+`ko_roman`(한글 배지)
  - `chapter_segments`, `thumb`, `desc`, `sub_replace`

### 3단계: 사용자 승인 단계 (필수 게이트)
- 대본 전체와 그림 목록(파일명 + 프롬프트/한 줄 설명)을 사용자에게 제시하고 승인을 받는다.
- 사용자가 수정을 요청하면 대본과 프롬프트를 보완한 후 승인을 거친다.

### 4단계: 이미지 생성 (그룹화 / 배치 방식)
- **그룹화(배치) 생성 원칙:** 이미지는 한 장씩 단건으로 생성하지 않고, **6장 단위 그룹(`--batch 6`)**으로 묶어서 실행한다. 세션 오버헤드(약 30k 토큰)를 1회만 지불하여 시간과 자원을 획기적으로 절약한다.
- **실행 명령:**
  ```powershell
  python oik_gen_codex.py ep0N.json --batch 6
  ```
- **화풍:** `ep01_images`와 동일한 **미니어처 종이공작·디오라마(Paper-craft diorama)** 톤 유지.
- **해상도:** 1536x1024 가로형 (16:9).
- **프롬프트 구성:**
  `STYLE_PRE_OBJECT` (사물) 또는 `STYLE_PRE` (인물·풍경) + `segment.prompt` + `STYLE_SUF`
- 생성된 이미지는 `ep0N_images/<img_name>.png`로 저장되며 순서와 품질을 검수한다.

### 5단계: 영상 조립 (`oik_build.py`)
PowerShell 환경에서 UTF-8 인코딩을 설정하고 조립 스크립트를 실행한다:
```powershell
$env:PYTHONIOENCODING='utf-8'; python oik_build.py ep0N.json
```
- 이미 음성이 모두 생성되어 있다면 `--skip-tts` 옵션으로 시간 단축 가능.
- 생성 결과물:
  - `EP0N_<Slug>_FINAL.mp4` (1080p 완성본, 하단 자막 번인 완료)
  - `EP0N_<Slug>_FINAL.en.srt` (참고용 SRT 자막)
  - `EP0N_<Slug>_FINAL_thumb.jpg` (1280x720 썸네일)
  - `EP0N_<Slug>_FINAL_description.txt` (유튜브 설명란 문안: 타임스탬프, 출처, 태그)

### 6단계: 검증 및 모바일 미리보기본 제작
1. **자막 겹침 검증:**
   - 도식(diagram) 및 카드(card) 요소가 위치하는 상단(y < 750~800px)과 하단 번인 자막(y 830~1000px) 사이에 최소 30px 이상의 여백(`gap_min` > 220)이 유지되는지 프레임 추출을 통해 확인한다.
2. **모바일 미리보기본 생성:**
   - 스마트폰 확인용 저용량(30MB 이하) 540p 사본 `EP0N_preview_540p.mp4`를 생성한다:
     ```powershell
     ffmpeg -y -i "EP0N_<Slug>_FINAL.mp4" -vf "scale=960:540" -c:v libx264 -crf 26 -c:a aac -b:a 64k "EP0N_preview_540p.mp4"
     ```
3. **사용자 보고:**
   - 영상 길이, 파일 용량 및 위치, 확인 완료 항목, 출처를 한국어 일상어로 명확히 보고한다.
