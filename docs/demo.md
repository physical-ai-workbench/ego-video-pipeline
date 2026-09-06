# Egocentric Video Annotation Tool

Egocentric Video에서 **Pick & Place 작업을 Episode / Action 단위로 Annotation**하고, 이를 구조화된 **Ground Truth Dataset**으로 구축하기 위한 도구입니다.

---

## Overview

Physical AI 및 로봇 학습에는 영상 속에서 **언제 어떤 작업이 수행되었는지 정의된 데이터**가 필요합니다.

본 프로젝트에서는 사람이 Egocentric Video를 직접 확인하면서 작업 구간을 정의하고,

```text id="9bhuj5"
Episode
└── Pick & Place
    ├── Pick
    ├── Move
    └── Place
```

형태로 Annotation할 수 있는 간단한 도구를 구현했습니다.

---

## Workflow

전체 데이터 구축 과정은 다음과 같습니다.

```text id="m23w6c"
Raw Egocentric Video
        ↓
Video Upload
        ↓
FFprobe
영상 정보 확인
        ↓
FFmpeg
영상 전처리
        ↓
Episode Segmentation
        ↓
Action Annotation
Pick / Move / Place
        ↓
CSV / JSON
        ↓
Ground Truth Dataset
```

---

## 1. Video Upload

Egocentric Video를 업로드하면 자동으로 Video ID를 부여하고 영상 정보를 확인합니다.

FFmpeg를 통해 Annotation에 사용할 영상 포맷으로 전처리합니다.

![Upload](docs/assets/sample.png)
![Upload](docs/assets/upload.png)

주요 영상 정보:

- Duration
- Resolution
- FPS
- Codec

---

## 2. Episode Annotation

영상에서 하나의 완전한 **Pick & Place 작업 구간**을 Episode로 정의합니다.

```text id="mh5yfe"
Video
│
├──────────── Episode 001 ────────────┤
│
│      Pick → Move → Place
│
└─────────────────────────────────────
```

Episode에는 다음 정보가 포함됩니다.

```text id="82t97f"
Episode ID
Start Time
End Time
Object
Description
```

---

## 3. Action Annotation

Episode 내부의 작업을 세부 Action으로 구분합니다.

현재 Annotation Label은 다음 세 가지입니다.

### Pick

물체를 집어 기존 위치에서 분리하는 동작

### Move

물체를 잡은 상태로 목표 위치까지 이동하는 동작

### Place

물체를 목표 위치에 놓고 손을 분리하는 동작

![Annotation](docs/assets/annotation.png)

최종적으로 하나의 Episode는 다음과 같이 구성됩니다.

```text id="kgn6vq"
Episode 001

Pick          Move                     Place
██████        ███████████████          ██████
```

---

## Demo

실제 Annotation 과정입니다.

![Demo](docs/assets/demo.gif)

```text id="pqiybw"
Video 선택
    ↓
Episode 구간 지정
    ↓
Pick
    ↓
Move
    ↓
Place
    ↓
Action Timeline
    ↓
Dataset 저장
```

---

## 4. Ground Truth Dataset

사람이 직접 Annotation한 결과는 **Ground Truth(정답 데이터)**로 저장됩니다.

![Dataset](docs/assets/dataset.png)

데이터 구조는 다음과 같습니다.

```text id="owr8pa"
Video
└── Episode
    ├── Pick
    ├── Move
    └── Place
```

저장 포맷:

```text id="gbd0xe"
videos.csv
episodes.csv
actions.csv
annotations.json
```

Dataset 화면에서는 전체 데이터를 확인하거나 **Video별로 필터링**하여 조회할 수 있습니다.

---

## Data Example

예를 들어 다음과 같이 Annotation됩니다.

| Video   | Episode | Action | Start     | End       | Object    | Hand  |
| ------- | ------- | ------ | --------- | --------- | --------- | ----- |
| ego_001 | ep_001  | Pick   | 00:03.200 | 00:04.500 | component | right |
| ego_001 | ep_001  | Move   | 00:04.500 | 00:08.000 | component | right |
| ego_001 | ep_001  | Place  | 00:08.000 | 00:09.500 | component | right |

이를 통해 영상 데이터를 모델 학습 및 평가에 활용할 수 있는 구조화된 데이터로 변환합니다.

---

## Tech Stack

```text id="skq7l3"
Python
Streamlit
Pandas
FFmpeg
FFprobe
```

각 기술의 역할은 다음과 같습니다.

| Technology | Role                     |
| ---------- | ------------------------ |
| Streamlit  | Annotation UI            |
| Python     | Application Logic        |
| Pandas     | Annotation Data 관리     |
| FFmpeg     | Video 전처리 / Clip 생성 |
| FFprobe    | Video Metadata 확인      |

---

## Test Dataset

테스트에는 Hugging Face의 `WhissleAI/egocentric-activity-sample` Dataset에서 **Pick & Place 샘플 영상**을 사용합니다.

https://huggingface.co/datasets/WhissleAI/egocentric-activity-sample

---

## Current Scope

현재 버전은 **Manual Annotation을 통한 Ground Truth Dataset 구축**을 목표로 합니다.

```text id="lhjfrh"
Current

Human
  ↓
Manual Annotation
  ↓
Ground Truth Dataset
```

향후에는 자동 Annotation을 추가하여 다음 구조로 확장할 수 있습니다.

```text id="ay2w1o"
Future

Ego Video
   ↓
AI Auto Annotation
   ↓
Episode / Action Prediction
   ↓
Human Review
   ↓
Ground Truth
   ↓
Model Evaluation / Training
```

즉, 현재 구축한 Manual Annotation Dataset을 기준 데이터로 활용하여 향후 **자동 Annotation 모델의 성능 평가 및 개선**으로 확장할 수 있습니다.

---

## Project Goal

> **Egocentric Video를 사람이 직접 Episode / Action 단위로 구조화하여, 향후 자동 Annotation 및 로봇 학습에 활용할 수 있는 Ground Truth Dataset 구축 프로세스를 구현합니다.**
