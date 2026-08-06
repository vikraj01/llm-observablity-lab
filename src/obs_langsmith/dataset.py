"""Create the golden dataset in LangSmith (run once).

Usage:
    uv run python -m src.obs_langsmith.dataset

These are our four standard test questions with reference answers.
The same cases get recreated in Langfuse in Phase 4 -- keeping them
identical is what makes the comparison fair.
"""

from dotenv import load_dotenv

load_dotenv()

from langsmith import Client  # noqa: E402

DATASET_NAME = "llm-obs-lab-golden"

EXAMPLES = [
    {
        "inputs": {"question": "what's 23*7?"},
        "outputs": {"answer": "161"},
    },
    {
        "inputs": {"question": "what's the weather in Chennai and what's 100/7?"},
        "outputs": {
            "answer": "Chennai is 22°C and humid; 100/7 is approximately 14.29."
        },
    },
    {
        "inputs": {"question": "what do my docs say about retries?"},
        "outputs": {
            "answer": (
                "Retry only idempotent operations, use exponential backoff "
                "with jitter, cap attempts at 3-5, retry on 429/5xx only "
                "(never 4xx), and log every retry attempt."
            )
        },
    },
    {
        "inputs": {
            "question": "weather in Mumbai, then multiply the temperature by 2"
        },
        "outputs": {
            "answer": (
                "States Mumbai's current temperature from the weather tool "
                "and gives that temperature multiplied by 2."
            )
        },
    },
]


def main() -> None:
    client = Client()
    if client.has_dataset(dataset_name=DATASET_NAME):
        print(f"dataset {DATASET_NAME!r} already exists -- nothing to do")
        return
    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description="Golden questions for the obs-lab agent (created in Phase 3)",
    )
    client.create_examples(dataset_id=dataset.id, examples=EXAMPLES)
    print(f"created dataset {DATASET_NAME!r} with {len(EXAMPLES)} examples")


if __name__ == "__main__":
    main()
