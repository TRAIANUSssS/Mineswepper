from tabulate import tabulate


def print_field(field):
    print("FIELD:")
    print(tabulate(field, tablefmt="plain", numalign="right"))


def print_mines(mine):
    print("\nINTERNAL MINES (1=mine, 0=not mine, -1=unknown):")
    print(tabulate(mine, tablefmt="plain", numalign="right"))


def print_actions(actions, limit=10):
    print("\nACTIONS:")
    if not actions:
        print("No actions found.")
        return

    for a in actions[:limit]:
        risk = getattr(a, "risk", None)
        if risk is None:
            print(a.kind, "cell", (a.r, a.c), "-", a.reason)
        else:
            print(a.kind, "cell", (a.r, a.c), f"risk={risk:.3f}", "-", a.reason)

