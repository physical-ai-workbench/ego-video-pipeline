# Annotation Schema

현재 Dataset은 **Pick & Place Task**를 대상으로 합니다.

## Hierarchy

```text
Video
└── Episode
    ├── Pick
    ├── Move
    └── Place
```

### Video

하나의 Egocentric 원본 영상을 의미합니다.

| Field             | Description   | Example        |
| ----------------- | ------------- | -------------- |
| video_id          | 영상 고유 ID  | ego_001        |
| original_filename | 원본 파일명   | sample.mp4     |
| task_type         | 영상 Task     | pick_and_place |
| duration          | 영상 길이(초) | 30.5           |
| fps               | FPS           | 30             |

### Episode

영상 내 하나의 완전한 Pick & Place 작업 구간입니다.

```text
Episode
└── Pick → Move → Place
```

| Field       | Description    | Example                  |
| ----------- | -------------- | ------------------------ |
| episode_id  | Episode ID     | ep_001                   |
| start_time  | 시작 시간(sec) | 3.200                    |
| end_time    | 종료 시간(sec) | 8.500                    |
| object      | 작업 대상      | component                |
| description | 추가 설명      | Pick and place component |

### Action

Episode를 구성하는 세부 동작입니다.

현재 Action Label은 다음 세 가지로 제한합니다.

| Action  | Definition                        |
| ------- | --------------------------------- |
| `pick`  | 물체를 집어 지지면에서 분리       |
| `move`  | 물체를 잡은 상태에서 이동         |
| `place` | 목표 위치에 물체를 놓고 손을 분리 |

예:

```text
Episode 001
00:03.200 ───────────────────── 00:08.500

Pick        Move               Place
██████      █████████████      ██████
```

### Object

현재 지원하는 Object Label:

```text
component
cup
bottle
box
tool
bolt
nut
container
other
```

### Hand

```text
right
left
both
none
```

## Time Format

내부 데이터는 초 단위 `float`로 저장합니다.

```text
1.000
12.350
63.500
```

UI에서는 가독성을 위해 다음 형식을 사용합니다.

```text
MM:SS.mmm
```

예:

```text
1.000 sec  → 00:01.000
12.350 sec → 00:12.350
63.500 sec → 01:03.500
```
