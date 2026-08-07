"""Create the golden dataset in Langfuse (run once).

Usage:
    uv run python -m src.obs_langfuse.dataset

Reuses the EXACT same examples as Phase 3 (imported from the LangSmith
module) so the two tools are compared on identical cases.
"""

from dotenv import load_dotenv

load_dotenv()

from langfuse import get_client  # noqa: E402

from ..obs_langsmith.dataset import EXAMPLES  # noqa: E402  (same 4 cases!)

DATASET_NAME = "llm-obs-lab-golden"


def main() -> None:
    langfuse = get_client()
    langfuse.create_dataset(
        name=DATASET_NAME,
        description="Golden questions for the obs-lab agent (mirror of the LangSmith dataset)",
    )
    for ex in EXAMPLES:
        langfuse.create_dataset_item(
            dataset_name=DATASET_NAME,
            input=ex["inputs"],
            expected_output=ex["outputs"],
        )
    langfuse.flush()
    print(f"created dataset {DATASET_NAME!r} with {len(EXAMPLES)} items")


if __name__ == "__main__":
    main()
