# Development Guide

Egocentric Video Annotation Tool의 **개발 구조, 데이터 흐름 및 주요 모듈**을 설명합니다.

---

## 1. Architecture

현재 프로젝트는 Streamlit 기반의 단일 애플리케이션이며 UI와 비즈니스 로직을 분리하여 구성합니다.

```text id="8h0a17"
                Streamlit UI
                     │
                     ▼
              ┌─────────────┐
              │   views/    │
              └──────┬──────┘
                     │
          ┌──────────┴──────────┐
          ▼                     ▼
┌──────────────────┐   ┌──────────────────┐
│ video_service.py │   │annotation_service│
└────────┬─────────┘   └────────┬─────────┘
         │                      │
         ▼                      ▼
 FFmpeg / FFprobe          Pandas / CSV
         │                      │
         ▼                      ▼
      Videos              Annotations
                                │
                                ▼
                              JSON
```

---

## 2. Project Structure

```text id="n59ax1"
ego-annotation/
│
├── app.py
├── config.py
├── requirements.txt
│
├── views/
│   ├── upload_view.py
│   ├── annotation_view.py
│   └── dataset_view.py
│
├── services/
│   ├── video_service.py
│   └── annotation_service.py
│
├── components/
│   ├── guide.py
│   └── timeline.py
│
├── utils/
│   ├── time_utils.py
│   └── state_utils.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── clips/
│
├── annotations/
│   ├── videos.csv
│   ├── episodes.csv
│   ├── actions.csv
│   └── annotations.json
│
└── docs/
```

---

## 3. Module Responsibilities

### `app.py`

Application Entry Point입니다.

담당 역할:

- Streamlit 초기 설정
- 기존 Video Registry 동기화
- 페이지 Navigation
- 각 View 호출

```text id="llz9kj"
app.py
  │
  ├── Upload
  ├── Annotation
  └── Dataset
```

비즈니스 로직은 `app.py`에 작성하지 않습니다.

---

### `config.py`

프로젝트 전역 설정을 관리합니다.

주요 설정:

```text id="79m1wg"
Directory Path
Task Type
FPS
Action Labels
Object Labels
Hand Labels
```

현재 Task:

```text id="20fvkl"
pick_and_place
```

현재 Action:

```text id="j5pf5c"
pick
move
place
```

새로운 Label이나 설정값은 가능하면 View에 직접 작성하지 않고 `config.py`에서 관리합니다.

---

## 4. Views

`views/`는 사용자에게 표시되는 화면을 담당합니다.

### `upload_view.py`

```text id="a2w77r"
Video Upload
    ↓
Raw Video 저장
    ↓
FFprobe
    ↓
FFmpeg Preprocessing
    ↓
Video Registry 등록
```

주요 기능:

- Video Upload
- Video ID 생성
- Metadata 확인
- Preprocessing
- Video 등록

---

### `annotation_view.py`

프로젝트의 핵심 Annotation 화면입니다.

```text id="iiz7hl"
Video 선택
    ↓
Episode 생성
    ↓
Episode Clip 생성
    ↓
Action 생성
    ↓
Pick / Move / Place
    ↓
Timeline 표시
```

Episode 및 Action의 생성·수정·삭제 UI를 담당합니다.

실제 데이터 처리는 `annotation_service.py`를 호출합니다.

---

### `dataset_view.py`

생성된 Ground Truth Dataset을 조회합니다.

주요 기능:

- 전체 Dataset 조회
- Video별 필터링
- Video / Episode / Action 통계
- Pagination
- JSON Preview

데이터가 증가해도 전체 데이터를 한 번에 화면에 표시하지 않도록 Pagination을 사용합니다.

---

## 5. Services

`services/`는 실제 데이터 처리 로직을 담당합니다.

### `video_service.py`

Video 관련 처리를 담당합니다.

```text id="3wsdmj"
Input Video
    │
    ├── FFprobe
    │      ↓
    │   Metadata
    │
    └── FFmpeg
           ↓
      Processed Video
```

주요 기능:

- Processed Video 검색
- Video ID 생성
- FFprobe 실행
- Video Metadata 추출
- FFmpeg Preprocessing
- Episode Clip 생성
- Episode Clip 삭제

FFmpeg / FFprobe는 Python Package가 아니라 **외부 실행 프로그램**입니다.

Python에서는 `subprocess`를 통해 호출합니다.

---

### `annotation_service.py`

Annotation 데이터 처리를 담당합니다.

주요 기능:

```text id="6c1xcl"
Video Registry
Episode CRUD
Action CRUD
Validation
CSV 저장
JSON 생성
```

Annotation View에서는 CSV 파일을 직접 수정하지 않고 이 Service를 통해 처리하는 것을 원칙으로 합니다.

---

## 6. Data Flow

전체 데이터 흐름은 다음과 같습니다.

```text id="i2scf7"
Uploaded Video
      │
      ▼
data/raw/
      │
      │ FFmpeg
      ▼
data/processed/
      │
      ├───────────────┐
      │               │
      ▼               ▼
Video Playback    videos.csv
      │
      ▼
Episode Annotation
      │
      ├───────────────┐
      ▼               ▼
episodes.csv      Episode Clip
                      │
                      ▼
                 data/clips/

Episode
   │
   ▼
Action Annotation
   │
   ▼
actions.csv
   │
   ▼
annotations.json
```

---

## 7. Video Processing

### FFprobe

업로드된 영상의 Metadata를 확인합니다.

확인 항목:

```text id="rzf91v"
Duration
Width
Height
FPS
Codec
```

---

### FFmpeg

영상 포맷을 Annotation 환경에 맞게 표준화합니다.

현재 기본 설정:

```text id="e70e89"
Resolution : 720p
FPS        : 30
Codec      : H.264
Audio      : AAC
```

개념적인 처리 과정:

```text id="tt0qrx"
Original Video
      ↓
FFmpeg
      ↓
720p / 30 FPS / H.264
      ↓
Processed Video
```

Episode 생성 시에는 해당 시간 범위의 별도 Clip도 생성합니다.

---

## 8. Annotation Data Model

데이터 구조는 3단계 계층입니다.

```text id="ztqkm6"
Video
└── Episode
    └── Action
```

관계로 표현하면:

```text id="0g0g4g"
Video 1 ─── N Episode

Episode 1 ─── N Action
```

---

### Video

영상 단위 Metadata입니다.

```text id="qxahfz"
video_id
original_filename
task_type
duration
width
height
fps
codec
created_at
```

예:

```text id="uoc7q7"
ego_001
```

---

### Episode

하나의 완전한 Pick & Place 작업입니다.

```text id="z8lns9"
episode_id
video_id
start_time
end_time
duration
object
description
```

예:

```text id="14smn7"
ego_001
└── ep_001
```

---

### Action

Episode 내부의 Atomic Action입니다.

```text id="jlh5uw"
action_id
episode_id
video_id
start_time
end_time
duration
action
object
hand
description
```

예:

```text id="hhq4eq"
ego_001
└── ep_001
    ├── act_001 : pick
    ├── act_002 : move
    └── act_003 : place
```

---

## 9. Storage

현재 버전에서는 별도의 Database를 사용하지 않습니다.

```text id="c2h6km"
Video Metadata   → videos.csv
Episode          → episodes.csv
Action           → actions.csv
Hierarchy        → annotations.json
```

현재 PoC 규모에서는 CSV / JSON으로 구조를 단순하게 유지합니다.

데이터 규모 또는 Multi-user 환경으로 확장할 경우 Database 도입을 검토할 수 있습니다.

---

## 10. CSV vs JSON

CSV는 데이터 관리 및 분석을 위해 사용합니다.

```text id="rh6zhw"
videos.csv
episodes.csv
actions.csv
```

JSON은 Video → Episode → Action 관계를 계층적으로 표현합니다.

```json id="6edz09"
{
  "video_id": "ego_001",
  "episodes": [
    {
      "episode_id": "ep_001",
      "actions": [
        {
          "action": "pick"
        },
        {
          "action": "move"
        },
        {
          "action": "place"
        }
      ]
    }
  ]
}
```

---

## 11. Validation

Annotation 데이터 품질을 위해 기본 Validation을 수행합니다.

### Action Range

Action은 Episode 범위를 벗어날 수 없습니다.

```text id="76mdhn"
Episode
|----------------------------|

Action
      |----------|

                OK
```

### Action Overlap

현재 Action끼리 시간 구간이 겹치는 것을 허용하지 않습니다.

```text id="mdxq36"
Pick
|----------|

       Move
       |----------|

       X
```

정상적인 예:

```text id="l5w7lm"
Pick       Move              Place
|--------| |---------------| |-------|
```

### Episode Update

이미 Action이 존재하는 Episode의 범위를 수정할 경우 기존 Action이 Episode 밖으로 나가게 되는 변경을 차단합니다.

---

## 12. State Management

Streamlit은 사용자 Interaction마다 Script를 다시 실행합니다.

따라서 중요한 데이터는 단순 Python 변수에만 저장하지 않습니다.

영구 데이터:

```text id="c2b5sa"
CSV
JSON
Video Files
```

화면 선택 상태:

```text id="o0qpt2"
URL Query Parameters
```

현재 유지하는 주요 상태:

```text id="eebqz7"
page
video
episode
dataset_video
```

예:

```text id="x87wuv"
?page=Annotation&video=ego_002&episode=ep_003
```

따라서 브라우저를 새로고침해도 현재 작업 위치를 복원할 수 있습니다.

---

## 13. Data Recovery

Application 시작 시 실제 `data/processed/` 영상과 `videos.csv`를 동기화합니다.

```text id="1gg85z"
data/processed/
       +
videos.csv
       ↓
sync_video_registry()
       ↓
Video Registry
```

예를 들어:

```text id="6s4sp3"
data/processed/

ego_001.mp4
ego_002.mp4
ego_003.mp4
```

가 존재하지만 `videos.csv`에 일부 Video가 누락된 경우 Registry를 자동으로 보완합니다.

이를 통해 서버를 종료하고 다시 실행해도 기존 Video 및 Annotation 데이터를 다시 사용할 수 있습니다.

---

## 14. Time Handling

시간은 내부적으로 **초 단위 float**로 저장합니다.

```text id="8rdt14"
1.0
12.35
63.5
```

UI에서는 다음 형식으로 변환하여 표시합니다.

```text id="b55yfb"
MM:SS.mmm
```

예:

```text id="x9fm5j"
1.0   → 00:01.000
12.35 → 00:12.350
63.5  → 01:03.500
```

현재 기준 영상 FPS는:

```text id="dmfplg"
30 FPS
```

따라서 한 Frame은 약:

```text id="pq5fwm"
1 / 30
≈ 0.033 sec
```

입니다.

---

## 15. Development Rules

기능 추가 시 아래 구조를 유지합니다.

```text id="wh0dkm"
UI
↓
views/

Reusable UI
↓
components/

Business Logic
↓
services/

Common Functions
↓
utils/

Configuration
↓
config.py
```

예를 들어 FFmpeg 기능을 추가할 경우:

```text id="zobp2d"
❌ annotation_view.py에서 직접 subprocess 실행

✅ annotation_view.py
        ↓
   video_service.py
        ↓
      FFmpeg
```

Annotation 저장도 동일합니다.

```text id="h0c04p"
❌ View에서 CSV 직접 수정

✅ View
    ↓
annotation_service
    ↓
CSV / JSON
```

---

## 16. Current Limitations

현재 버전은 빠른 Ground Truth 구축을 위한 PoC이므로 다음 제한이 있습니다.

- Pick & Place Task만 지원
- Single-user 기준
- CSV / JSON 기반 저장
- Streamlit 기본 Video Player 사용
- Manual Annotation 중심
- Local Video Storage 사용
- 별도의 Authentication 없음

---

## 17. Future Architecture

다음 단계에서는 자동 Annotation을 추가할 수 있습니다.

```text id="5bq8jv"
                    Ego Video
                        │
                        ▼
                Auto Annotation
                        │
                ┌───────┴───────┐
                ▼               ▼
         Episode Prediction   Action Prediction
                │               │
                └───────┬───────┘
                        ▼
                   Streamlit UI
                        │
              Accept / Modify / Reject
                        │
                        ▼
                 Reviewed Dataset
                        │
                        ▼
                  Model Training
```

추가 검토 영역:

```text id="l34eb5"
Custom Video Component
Frame-level Annotation
Auto Episode Segmentation
VLM Annotation
Human-in-the-loop
Model Evaluation
Database
Object Storage
Multi-user
```

---

## Summary

현재 구조의 핵심은 다음과 같습니다.

```text id="u6hp9f"
Streamlit
   ↓
Views
   ↓
Services
   ↓
FFmpeg / Pandas
   ↓
Video + CSV + JSON
```

UI, 영상 처리, Annotation 로직, 저장 로직을 분리하여 **현재 Manual Annotation PoC를 유지하면서 향후 Auto Annotation 및 VLM 기반 파이프라인으로 확장할 수 있도록 구성합니다.**
