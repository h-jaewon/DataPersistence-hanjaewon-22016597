from database import get_connection
from models import Order, StateHistory
from state_machine import State, can_transition


def create_order(name: str) -> Order:
    with get_connection() as conn:
        cursor = conn.execute(
            "INSERT INTO orders (name) VALUES (?)", (name,)
        )
        order_id = cursor.lastrowid
        # 최초 상태도 이력에 기록
        conn.execute(
            "INSERT INTO state_history (order_id, from_state, to_state) VALUES (?, ?, ?)",
            (order_id, None, State.ORDERED.value),
        )
        row = conn.execute(
            "SELECT * FROM orders WHERE id = ?", (order_id,)
        ).fetchone()
    return Order.from_row(row)


def get_in_progress_orders(limit: int = 5) -> list[Order]:
    """최종 상태가 아닌 주문을 최근 상태 변경 순으로 반환."""
    final_states = ("배송완료", "취소됨")
    placeholders = ",".join("?" * len(final_states))
    with get_connection() as conn:
        rows = conn.execute(
            f"""
            SELECT o.*
            FROM orders o
            JOIN (
                SELECT order_id, MAX(id) AS last_id
                FROM state_history
                GROUP BY order_id
            ) h ON o.id = h.order_id
            WHERE o.state NOT IN ({placeholders})
            ORDER BY h.last_id DESC
            LIMIT ?
            """,
            (*final_states, limit),
        ).fetchall()
    return [Order.from_row(r) for r in rows]


def get_all_orders() -> list[Order]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM orders ORDER BY id"
        ).fetchall()
    return [Order.from_row(r) for r in rows]


def get_order(order_id: int) -> Order | None:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM orders WHERE id = ?", (order_id,)
        ).fetchone()
        if not row:
            return None
        order = Order.from_row(row)

        history_rows = conn.execute(
            "SELECT * FROM state_history WHERE order_id = ? ORDER BY id",
            (order_id,),
        ).fetchall()
        order.history = [
            StateHistory(
                from_state=h["from_state"],
                to_state=h["to_state"],
                changed_at=h["changed_at"],
            )
            for h in history_rows
        ]
    return order


def advance_state(order_id: int, target: State) -> tuple[Order | None, str]:
    """상태를 전이한다. 실패 시 (None, 오류메시지) 반환."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM orders WHERE id = ?", (order_id,)
        ).fetchone()
        if not row:
            return None, f"ID {order_id} 주문을 찾을 수 없습니다."

        current = State(row["state"])
        if not can_transition(current, target):
            return None, f"[{current.value}] 상태에서 [{target.value}]으로 전이할 수 없습니다."

        conn.execute(
            "UPDATE orders SET state = ? WHERE id = ?",
            (target.value, order_id),
        )
        conn.execute(
            "INSERT INTO state_history (order_id, from_state, to_state) VALUES (?, ?, ?)",
            (order_id, current.value, target.value),
        )
        row = conn.execute(
            "SELECT * FROM orders WHERE id = ?", (order_id,)
        ).fetchone()
    return Order.from_row(row), ""
