# Egocentric Video Annotation Tool

Egocentric Video의 **Pick & Place 작업을 Episode / Action 단위로 Annotation**하고 Ground Truth Dataset을 구축하기 위한 Streamlit 기반 도구입니다.

## Features

- Egocentric Video 업로드 및 관리
- FFprobe 기반 영상 정보 확인
- FFmpeg 기반 영상 전처리
- Pick & Place Episode 구간 Annotation
- Pick / Move / Place Action Annotation
- Episode Clip 생성
- CSV / JSON Ground Truth 저장
- 영상별 Annotation Dataset 조회

---

## Demo

<!-- 캡처 이미지 추가 후 사용 -->

```text
docs/assets/
├── upload.png
├── annotation.png
├── dataset.png
└── demo.gif
```

```markdown
![Demo](docs/assets/demo.gif)
```

---

## Test Video

테스트 영상은 Hugging Face의 `WhissleAI/egocentric-activity-sample` Dataset에서 **Pick & Place 샘플 영상**을 사용할 수 있습니다.

https://huggingface.co/datasets/WhissleAI/egocentric-activity-sample

---

## Requirements

- Python 3.10+
- FFmpeg / FFprobe

FFmpeg는 Python 패키지가 아니므로 `requirements.txt`와 별도로 설치해야 합니다.

---

# macOS

### 1. FFmpeg 설치

Homebrew를 이용하여 설치합니다.

```bash
brew install ffmpeg
```

설치 확인:

```bash
ffmpeg -version
ffprobe -version
```

### 2. Virtual Environment 생성

```bash
python3 -m venv .venv
```

활성화:

```bash
source .venv/bin/activate
```

### 3. Python Package 설치

```bash
pip install -r requirements.txt
```

### 4. 실행

```bash
streamlit run app.py
```

---

# Windows

### 1. FFmpeg 설치

Windows Package Manager를 사용할 수 있는 경우:

```powershell
winget search ffmpeg
```

사용 가능한 FFmpeg 패키지를 확인한 후 설치합니다.

설치 후 새 터미널에서 확인합니다.

```powershell
ffmpeg -version
ffprobe -version
```

직접 설치하는 경우 `ffmpeg.exe`, `ffprobe.exe`가 위치한 `bin` 디렉터리를 Windows `PATH`에 등록해야 합니다.

> 회사 PC에서는 소프트웨어 설치 및 PATH 변경 전 사내 IT/보안 정책을 확인하세요.

### 2. Virtual Environment 생성

```powershell
python -m venv .venv
```

PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

CMD:

```cmd
.venv\Scripts\activate
```

### 3. Python Package 설치

```powershell
pip install -r requirements.txt
```

### 4. 실행

```powershell
streamlit run app.py
```

---

## Annotation Flow

```text
Raw Egocentric Video
        ↓
Upload
        ↓
FFprobe
        ↓
FFmpeg Preprocessing
        ↓
Pick & Place Episode
        ↓
Pick / Move / Place
        ↓
CSV / JSON
        ↓
Ground Truth Dataset
```

현재 버전은 **Pick & Place Task**를 대상으로 합니다.

### Annotation Structure

```text
Video
└── Episode (Pick & Place)
    ├── Pick
    ├── Move
    └── Place
```

- **Video**: 하나의 Egocentric 원본 영상
- **Episode**: 하나의 완전한 Pick & Place 작업 구간
- **Action**: Episode를 구성하는 Pick / Move / Place 세부 동작

---

## Project Structure

```text
ego-annotation/
├── app.py
├── config.py
├── requirements.txt
├── README.md
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
├── docs/
│   ├── schema.md
│   ├── annotation-guide.md
│   └── assets/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── clips/
│
└── annotations/
    ├── videos.csv
    ├── episodes.csv
    ├── actions.csv
    └── annotations.json
```

---

## Documentation

상세 Annotation 기준 및 데이터 구조는 `docs/`에서 관리합니다.

- `docs/schema.md` — Video / Episode / Action Schema 및 Label 정의
- `docs/annotation-guide.md` — Pick / Move / Place Annotation 기준

---

## Dependencies

Python 패키지는 `requirements.txt`로 관리합니다.

```text
streamlit>=1.40,<2.0
pandas>=2.0,<3.0
```

FFmpeg / FFprobe는 별도로 설치해야 합니다.
