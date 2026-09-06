# Annotation Guide

## Current Scope

현재 Annotation 대상 Task는 **Pick & Place**입니다.

```text
Pick → Move → Place
```

## Episode

하나의 Pick & Place 작업 전체를 하나의 Episode로 정의합니다.

### Start

작업 대상 물체를 Pick하기 위한 명확한 행동이 시작되는 시점입니다.

### End

물체를 목표 위치에 Place하고 손이 물체에서 분리되어 작업이 완료된 시점입니다.

---

## Pick

물체를 집어 기존 지지면에서 분리하는 동작입니다.

```text
손 접근 → 물체 Grasp → 물체가 지지면에서 분리
```

---

## Move

물체를 잡은 상태로 기존 위치에서 목표 위치까지 이동하는 동작입니다.

```text
Pick 완료 → 물체 이동 → Place 시작
```

---

## Place

물체를 목표 위치에 내려놓고 손을 분리하는 동작입니다.

```text
물체 접촉 → 내려놓기 → 손 분리
```

---

## Annotation Rules

- 하나의 Episode는 하나의 완전한 Pick & Place 작업을 의미합니다.
- Action은 반드시 Episode 범위 안에 있어야 합니다.
- Action 구간끼리는 겹치지 않도록 합니다.
- 동일한 행동에는 항상 동일한 Label을 사용합니다.
- `pick`, `move`, `place` 외 임의의 Action 이름을 생성하지 않습니다.
- Object는 정의된 Label을 우선 사용하고 분류하기 어려운 경우 `other`를 사용합니다.
- 애매한 경계도 전체 Dataset에서 최대한 동일한 기준을 적용합니다.
