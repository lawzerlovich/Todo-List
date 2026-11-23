import json
import os
import sys

DATA_FILE = "todo_data.json"


def is_valid_task(item):
    """Check if a task dictionary has valid types and non-empty task text."""
    if not isinstance(item, dict):
        return False

    task_id = item.get("id")
    task_text = item.get("task")
    done = item.get("done")

    valid_id = isinstance(task_id, int) and not isinstance(task_id, bool) and task_id > 0
    valid_text = isinstance(task_text, str) and task_text.strip() != ""
    valid_done = isinstance(done, bool)

    return valid_id and valid_text and valid_done


def load_data(filename=DATA_FILE):
    """Load tasks, next_id, and malformed entries; report tampering."""
    data = {"next_id": 1, "tasks": [], "malformed": []}

    if not os.path.exists(filename):
        return data

    try:
        with open(filename, "r", encoding="utf-8") as f:
            raw = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"[File Error] Cannot read '{filename}': {e}")
        sys.exit(2)

    if not isinstance(raw, dict):
        print(f"[File Error] '{filename}' must contain a JSON object.")
        sys.exit(2)

    raw_tasks = raw.get("tasks", [])
    if not isinstance(raw_tasks, list):
        print(f"[File Error] 'tasks' in '{filename}' must be a list.")
        sys.exit(2)

    malformed = []
    tamper_messages = []

    # Preserve previously recorded malformed entries
    prev_malformed = raw.get("malformed", [])
    if isinstance(prev_malformed, list):
        malformed.extend(prev_malformed)

    valid_tasks = []
    seen_ids = set()

    for item in raw_tasks:
        if is_valid_task(item) and item["id"] not in seen_ids:
            valid_tasks.append({
                "id": item["id"],
                "task": item["task"],
                "done": item["done"],
            })
            seen_ids.add(item["id"])
        else:
            malformed.append(item)
            tamper_messages.append(f"Invalid or duplicate task entry: {item!r}")

    # Check if next_id was tampered with
    highest_id = max(seen_ids) if seen_ids else 0
    min_required_next_id = highest_id + 1
    saved_next_id = raw.get("next_id", 1)

    if not isinstance(saved_next_id, int) or isinstance(saved_next_id, bool) or saved_next_id < 1:
        tamper_messages.append(f"Invalid 'next_id' value ({saved_next_id!r}); resetting safely.")
        next_id = min_required_next_id
    elif saved_next_id < min_required_next_id:
        tamper_messages.append(
            f"'next_id' ({saved_next_id}) was lower than needed ({min_required_next_id}); bumping to prevent ID reuse."
        )
        next_id = min_required_next_id
    else:
        next_id = saved_next_id

    if tamper_messages:
        print("[Tamper Warning] Outside tampering detected:")
        for msg in tamper_messages:
            print(f"  - {msg}")
        print("  Malformed entries are ignored in the list, but preserved.")

    return {
        "next_id": next_id,
        "tasks": valid_tasks,
        "malformed": malformed,
    }


def save_data(data, filename=DATA_FILE):
    """Save current state to disk. Exits with code 2 on file write failure."""
    payload = {
        "next_id": data["next_id"],
        "tasks": data["tasks"],
        "malformed": data["malformed"],
    }
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
    except OSError as e:
        print(f"[File Error] Cannot save '{filename}': {e}")
        sys.exit(2)


def show_menu():
    print("\n TODO LIST MENU ")
    print("1. View tasks")
    print("2. Add task")
    print("3. Mark task as done")
    print("4. Delete task")
    print("5. Save and exit")


def view_tasks(data):
    print("\n Your Tasks ")
    if not data["tasks"]:
        print("(No tasks yet)")
        return
    for num, t in enumerate(data["tasks"], start=1):
        mark = "✓ " if t["done"] else ""
        print(f"{num}. {mark}{t['task']}")


def add_task(data):
    text = input("Enter new task: ").strip()
    if not text:
        print("[Input Error] Task cannot be empty.")
        sys.exit(1)

    task = {"id": data["next_id"], "task": text, "done": False}
    data["tasks"].append(task)
    data["next_id"] += 1
    print(f'"{text}"')


def ask_task_number(total):
    raw = input("Enter task number: ").strip()
    try:
        num = int(raw)
        if num < 1 or num > total:
            raise ValueError
        return num
    except ValueError:
        print(f"[Input Error] Please enter a number from 1 to {total}.")
        sys.exit(1)


def mark_done(data):
    if not data["tasks"]:
        print("No tasks to complete.")
        return
    view_tasks(data)
    num = ask_task_number(len(data["tasks"]))
    data["tasks"][num - 1]["done"] = True
    print(f'Marked "{data["tasks"][num - 1]["task"]}" as done.')


def delete_task(data):
    if not data["tasks"]:
        print("No tasks to delete.")
        return
    view_tasks(data)
    num = ask_task_number(len(data["tasks"]))
    removed = data["tasks"].pop(num - 1)
    print(f'Deleted "{removed["task"]}".')


def main():
    data = load_data()
    exit_code = 0

    try:
        while True:
            show_menu()
            choice = input("Choose an option (1-5): ").strip().lower()

            if choice in ("1", "view", "list"):
                view_tasks(data)
            elif choice in ("2", "add"):
                add_task(data)
            elif choice in ("3", "done"):
                mark_done(data)
            elif choice in ("4", "delete", "del"):
                delete_task(data)
            elif choice in ("5", "exit", "quit", "q"):
                print("Saved.")
                exit_code = 0
                break
            else:
                print("[Input Error] Invalid menu choice. Please pick 1-5.")
                exit_code = 1
                break
    except SystemExit as e:
        
        exit_code = e.code if isinstance(e.code, int) else 1
    except KeyboardInterrupt:
        print("\nInterrupted. Saving before exit...")
        exit_code = 0
    finally:
        
        save_data(data)

    sys.exit(exit_code)


if __name__ == "__main__":
    main()