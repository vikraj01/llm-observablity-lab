import sys

from dotenv import load_dotenv

load_dotenv()

from .graph import graph


def main() -> None:
    if len(sys.argv) < 2:
        print('usage: python -m src.agent "your question"')
        return

    question = " ".join(sys.argv[1:])
    result = graph.invoke({"messages": [("user", question)]})

    print("\n=== full message trace ===")
    for msg in result["messages"]:
        msg.pretty_print()

    print("\n=== final answer ===")
    print(result["messages"][-1].content)


if __name__ == "__main__":
    main()
