# 주문 상태 관리 PoC — 데이터 영속성 실습

> **학번:** 22016597 &nbsp;|&nbsp; **이름:** 한재원

SQLite를 이용한 **데이터 영속성(Data Persistence)** 실습 프로젝트입니다.  
주문의 상태 변화를 상태 머신(State Machine)으로 모델링하고, 프로그램을 종료·재시작해도 모든 상태 이력이 그대로 유지되는 것을 확인합니다.

---

## 핵심 개념

| 개념 | 설명 |
|------|------|
| **데이터 영속성** | 프로세스가 종료되어도 데이터가 소멸되지 않고 디스크(SQLite)에 보존됨 |
| **상태 머신** | 유효한 전이(Transition)만 허용하는 규칙 기반 상태 관리 |
| **상태 이력** | 모든 상태 변경을 별도 테이블에 append-only 방식으로 기록 |

---

## 주문 상태 흐름

```
주문접수 ──► 결제완료 ──► 준비중 ──► 배송중 ──► 배송완료
   │             │           │
   └─────────────┴───────────┴──────────────────► 취소됨
```

- **배송완료**, **취소됨** 은 최종 상태로 더 이상 전이되지 않습니다.

---

## 프로젝트 구조

```
order-poc/
├── cli.py            # 대화형 CLI 진입점
├── repository.py     # DB 접근 계층 (CRUD + 상태 전이)
├── models.py         # 데이터 모델 (Order, StateHistory)
├── state_machine.py  # 상태 열거형 및 전이 규칙
├── database.py       # SQLite 연결 및 테이블 초기화
└── orders.db         # 자동 생성되는 SQLite 데이터베이스
```

### 계층 구조

```
CLI (cli.py)
  └─► Repository (repository.py)   ← 비즈니스 로직 + 영속성
        ├─► Database (database.py)  ← SQLite 연결
        ├─► Models (models.py)      ← 데이터 구조
        └─► StateMachine (state_machine.py) ← 전이 규칙
```

---

## DB 스키마

```sql
-- 주문 테이블
CREATE TABLE orders (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    state      TEXT    NOT NULL DEFAULT '주문접수',
    created_at TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

-- 상태 변경 이력 테이블 (영속성의 핵심)
CREATE TABLE state_history (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id   INTEGER NOT NULL,
    from_state TEXT,
    to_state   TEXT    NOT NULL,
    changed_at TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (order_id) REFERENCES orders(id)
);
```

---

## 실행 방법

**요구 사항:** Python 3.10 이상 (외부 패키지 없음)

```bash
python cli.py
```

최초 실행 시 `orders.db` 파일이 자동으로 생성됩니다.  
프로그램을 종료 후 다시 실행하면 이전 데이터가 그대로 복원됩니다.

---

## CLI 명령어

| 명령어 | 설명 | 예시 |
|--------|------|------|
| `list` | 전체 주문 목록 조회 | `list` |
| `new <주문명>` | 새 주문 생성 | `new 노트북 주문` |
| `show <ID>` | 주문 상세 및 상태 이력 조회 | `show 1` |
| `next <ID>` | 다음 상태로 전진 (선택 메뉴 제공) | `next 1` |
| `help` | 명령어 목록 출력 | `help` |
| `quit` | 프로그램 종료 | `quit` |

### 실행 예시

```
=== 주문 상태 관리 PoC (종료: quit) ===
  [핵심] 종료 후 재시작해도 상태가 그대로 유지됩니다.

>>> new 노트북 주문
  생성됨: [주문 #1] 노트북 주문  |  현재 상태: 【주문접수】

>>> next 1
  현재 상태: 【주문접수】
  다음 단계를 선택하세요:
    1. 결제완료
    2. 취소됨
  번호 입력 (취소: Enter): 1

  상태 전이 완료:
  【주문접수】 -> 【결제완료】

>>> show 1
  [주문 #1] 노트북 주문  |  현재 상태: 【결제완료】

  --- 상태 이력 ---
   2026-05-08 12:00:00  주문접수
   2026-05-08 12:00:05  주문접수 -> 결제완료

  --- 가능한 다음 단계 ---
  1. 준비중
  2. 취소됨
```

---

## 영속성 확인 방법

1. `new` 명령으로 주문을 생성하고 `next`로 상태를 몇 번 변경합니다.
2. `quit`으로 프로그램을 종료합니다.
3. 다시 `python cli.py`를 실행합니다.
4. 시작 화면에 **"이전에 진행 중이던 주문"** 목록이 표시되며, `show` 명령으로 이력이 그대로 보존됨을 확인할 수 있습니다.
