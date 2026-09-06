# Git Convention

## 1. Basic Workflow

기능 추가 및 코드 수정 후 아래 순서로 커밋 및 Push한다.

```bash
git status
git add .
git commit -m "<type>: <message>"
git push
```

---

## 2. Commit Message

커밋 메시지는 아래 형식을 사용한다.

```text
<type>: <message>
```

### Types

| Type       | Description         | Example                               |
| ---------- | ------------------- | ------------------------------------- |
| `feat`     | 새로운 기능 추가    | `feat: add video annotation`          |
| `fix`      | 버그 수정           | `fix: fix annotation save error`      |
| `docs`     | 문서 수정           | `docs: update README`                 |
| `refactor` | 코드 구조 개선      | `refactor: simplify annotation logic` |
| `chore`    | 설정 및 기타 작업   | `chore: update gitignore`             |
| `test`     | 테스트 추가 및 수정 | `test: add annotation tests`          |

### Rules

- 영어 소문자를 기본으로 사용한다.
- 메시지는 간결하게 작성한다.
- 무엇을 변경했는지 명확하게 작성한다.
- 하나의 커밋에는 하나의 목적을 담는다.

---

## 3. Branch

기본 브랜치는 `main`을 사용한다.

```text
main
```

개인 PoC 단계에서는 별도의 브랜치를 만들지 않고 `main`에서 작업한다.

프로젝트 규모가 커질 경우 기능별 브랜치를 사용한다.

```text
main
├── feature/video-preprocessing
├── feature/annotation-ui
└── fix/annotation-save
```

---

## 4. Push Workflow

작업 완료 후 변경사항을 확인한다.

```bash
git status
```

변경사항을 Stage에 추가한다.

```bash
git add .
```

커밋한다.

```bash
git commit -m "feat: add video preprocessing"
```

GitHub에 Push한다.

```bash
git push
```

---

## 5. Files Not Tracked by Git

대용량 영상, 가상환경, 캐시 및 로컬 생성 파일은 Git에 포함하지 않는다.

`.gitignore` 예시:

```gitignore
# Python
.venv/
__pycache__/
*.pyc

# macOS
.DS_Store

# Video Data
data/raw/
data/processed/
data/clips/

# Environment
.env
```
