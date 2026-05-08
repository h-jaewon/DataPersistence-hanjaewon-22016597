from dataclasses import dataclass, field
from state_machine import State


@dataclass
class StateHistory:
    from_state: str | None
    to_state: str
    changed_at: str

    def __str__(self) -> str:
        arrow = f"{self.from_state} -> " if self.from_state else ""
        return f"  {self.changed_at}  {arrow}{self.to_state}"


@dataclass
class Order:
    id: int
    name: str
    state: State
    created_at: str
    history: list[StateHistory] = field(default_factory=list)

    @staticmethod
    def from_row(row) -> "Order":
        return Order(
            id=row["id"],
            name=row["name"],
            state=State(row["state"]),
            created_at=row["created_at"],
        )

    def summary(self) -> str:
        return f"[주문 #{self.id}] {self.name}  |  현재 상태: 【{self.state.value}】"
