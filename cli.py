import sys
sys.stdout.reconfigure(encoding="utf-8")

import database
import repository as repo
from state_machine import State, next_states, is_final


def resume_prompt() -> int | None:
    """시작 시 진행 중인 주문을 보여주고, 이어서 볼 주문 ID를 반환. 없거나 선택 안 하면 None."""
    orders = repo.get_in_progress_orders()
    if not orders:
        return None

    print("\n  --- 이전에 진행 중이던 주문 ---")
    for i, o in enumerate(orders, 1):
        print(f"  {i}. {o.summary()}")
    print()

    raw = input("  이어서 작업할 주문 번호를 선택하세요 (없으면 Enter): ").strip()
    if not raw:
        return None
    if raw.isdigit() and 1 <= int(raw) <= len(orders):
        return orders[int(raw) - 1].id
    return None


def show_help() -> None:
    print("""
  명령어 목록:
    list                전체 주문 목록
    new <주문명>         주문 생성
    show <ID>           주문 상세 + 상태 이력
    next <ID>           다음 단계로 전진
    quit                종료
""")


def print_order_list() -> None:
    orders = repo.get_all_orders()
    if not orders:
        print("  (주문 없음)")
        return
    for o in orders:
        final_mark = "  [완료]" if is_final(o.state) else ""
        print(f"  {o.summary()}{final_mark}")


def print_order_detail(order_id: int) -> None:
    order = repo.get_order(order_id)
    if not order:
        print(f"  [오류] ID {order_id} 주문을 찾을 수 없습니다.")
        return

    print(f"\n  {order.summary()}")
    print()
    print("  --- 상태 이력 ---")
    for h in order.history:
        print(f" {h}")
    print()

    nexts = next_states(order.state)
    if nexts:
        print("  --- 가능한 다음 단계 ---")
        for i, s in enumerate(nexts, 1):
            print(f"  {i}. {s.value}")
    else:
        print("  (이 주문은 최종 상태입니다)")
    print()


def do_next(order_id: int) -> None:
    order = repo.get_order(order_id)
    if not order:
        print(f"  [오류] ID {order_id} 주문을 찾을 수 없습니다.")
        return

    nexts = next_states(order.state)
    if not nexts:
        print(f"  이미 최종 상태입니다: 【{order.state.value}】")
        return

    print(f"\n  현재 상태: 【{order.state.value}】")
    print("  다음 단계를 선택하세요:")
    for i, s in enumerate(nexts, 1):
        print(f"    {i}. {s.value}")

    raw = input("  번호 입력 (취소: Enter): ").strip()
    if not raw:
        print("  취소됨.")
        return

    if not raw.isdigit() or not (1 <= int(raw) <= len(nexts)):
        print("  [오류] 올바른 번호를 입력해주세요.")
        return

    target = nexts[int(raw) - 1]
    updated, err = repo.advance_state(order_id, target)
    if err:
        print(f"  [오류] {err}")
    else:
        print(f"\n  상태 전이 완료:")
        print(f"  【{order.state.value}】 -> 【{updated.state.value}】")
        if is_final(updated.state):
            print(f"  이 주문은 최종 상태에 도달했습니다.")
    print()


def main() -> None:
    database.init_db()
    print("=== 주문 상태 관리 PoC (종료: quit) ===")
    print("  [핵심] 종료 후 재시작해도 상태가 그대로 유지됩니다.")

    resume_id = resume_prompt()
    if resume_id is not None:
        print()
        print_order_detail(resume_id)
    else:
        show_help()

    while True:
        try:
            raw = input(">>> ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not raw:
            continue

        parts = raw.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""

        if cmd in ("quit", "exit", "q"):
            print("종료합니다. 데이터는 orders.db에 저장되어 있습니다.")
            break

        elif cmd == "list":
            print()
            print_order_list()
            print()

        elif cmd == "new":
            if not arg:
                print("  [오류] 주문명을 입력해주세요. 예: new 노트북 주문")
                continue
            order = repo.create_order(arg)
            print(f"\n  생성됨: {order.summary()}\n")

        elif cmd == "show":
            if not arg.isdigit():
                print("  [오류] 예: show 1")
                continue
            print_order_detail(int(arg))

        elif cmd == "next":
            if not arg.isdigit():
                print("  [오류] 예: next 1")
                continue
            do_next(int(arg))

        elif cmd == "help":
            show_help()

        else:
            print(f"  [오류] 알 수 없는 명령어: {cmd}")


if __name__ == "__main__":
    main()
