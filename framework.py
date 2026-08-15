from pathlib import Path
import shutil, sys

F = Path.home()/".richmack"/"framework"
F.mkdir(parents=True, exist_ok=True)

cmd = sys.argv[1] if len(sys.argv) > 1 else ""
arg = " ".join(sys.argv[2:])

if cmd == "add":
    p = Path(arg)
    shutil.copy(p, F/p.name)
    print(f"Added: {p.name}")

elif cmd == "list":
    for p in F.iterdir():
        print(p.name)

elif cmd == "show":
    print((F/arg).read_text())

elif cmd == "search":
    for p in F.iterdir():
        if p.is_file() and arg.lower() in p.read_text(errors="ignore").lower():
            print(p.name)

else:
    print("Usage: framework.py add|list|show|search ARG")
