from enum import Enum


class State(str, Enum):
    ORDERED   = "주문접수"
    PAID      = "결제완료"
    PREPARING = "준비중"
    SHIPPING  = "배송중"
    DELIVERED = "배송완료"
    CANCELLED = "취소됨"


# 각 상태에서 전이할 수 있는 다음 상태 목록
TRANSITIONS: dict[State, list[State]] = {
    State.ORDERED:   [State.PAID,      State.CANCELLED],
    State.PAID:      [State.PREPARING, State.CANCELLED],
    State.PREPARING: [State.SHIPPING,  State.CANCELLED],
    State.SHIPPING:  [State.DELIVERED],
    State.DELIVERED: [],   # 최종 상태 - 전이 불가
    State.CANCELLED: [],   # 최종 상태 - 전이 불가
}


def next_states(current: State) -> list[State]:
    return TRANSITIONS[current]


def can_transition(current: State, target: State) -> bool:
    return target in TRANSITIONS[current]


def is_final(state: State) -> bool:
    return len(TRANSITIONS[state]) == 0
