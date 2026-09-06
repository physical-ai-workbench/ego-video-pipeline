# Egocentric Video Annotation Tool

Egocentric Video의 **Pick & Place 작업 구간을 Episode / Action 단위로 Annotation**하기 위한 Streamlit 기반 도구입니다.

주요 기능:

- Egocentric Video 업로드
- FFprobe 기반 영상 정보 확인
- FFmpeg 기반 영상 전처리
- Episode 구간 Annotation
- Pick / Move / Place Action Annotation
- Episode Clip 생성
- CSV / JSON Ground Truth 저장

---

## Project Structure

```text
ego-annotation/
├── app.py
├── config.py
├── requirements.txt
│
├── views/
├── services/
├── components/
├── utils/
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
```

---

# Setup

Python 3.10 이상을 권장합니다.

또한 영상 처리를 위해 **FFmpeg / FFprobe 설치가 필요합니다.**

---

## macOS

### 1. FFmpeg 설치

Homebrew가 설치되어 있다면:

```bash
brew install ffmpeg
```

설치 확인:

```bash
ffmpeg -version
ffprobe -version
```

### 2. Virtual Environment 생성

프로젝트 폴더에서:

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

브라우저에서 Streamlit 화면이 자동으로 실행됩니다.

---

## Windows

### 1. FFmpeg 설치

FFmpeg를 설치한 뒤 `ffmpeg`와 `ffprobe`가 PATH에 등록되어 있어야 합니다.

#### [ 방법 A. winget 사용 ]

PowerShell 또는 CMD에서:

```
winget search ffmpeg
```

사용 가능한 FFmpeg 패키지를 확인한 후 승인된 패키지를 설치합니다.

#### [ 방법 B. 직접 설치 ]

FFmpeg binary를 다운로드하여 설치한 뒤 ffmpeg.exe와 ffprobe.exe가 위치한 bin 디렉터리를 Windows PATH에 등록합니다.

설치가 완료되면 새 CMD 또는 PowerShell에서:

CMD 또는 PowerShell에서 확인:

```powershell
ffmpeg -version
ffprobe -version
```

### 2. Virtual Environment 생성

```powershell
python -m venv .venv
```

PowerShell 활성화:

```powershell
.\.venv\Scripts\Activate.ps1
```

CMD 활성화:

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

# Annotation Flow

```text
Raw Ego Video
      ↓
Upload
      ↓
FFprobe
      ↓
FFmpeg Preprocessing
      ↓
Episode Segmentation
      ↓
Pick / Move / Place Annotation
      ↓
CSV / JSON
      ↓
Ground Truth Dataset
```

현재 버전은 **Pick & Place Task**를 대상으로 합니다.

# Documentation

Annotation 데이터 구조와 작업 기준은 docs/에서 관리합니다.

docs/schema.md — Video / Episode / Action 데이터 구조 및 Label 정의
docs/annotation-guide.md — Pick / Move / Place Annotation 작업 기준
