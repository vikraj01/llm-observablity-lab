"""Run an LLM-as-judge evaluation over the golden dataset.

Usage:
    uv run python -m src.obs_langsmith.evaluate

What happens:
- LangSmith pulls each example from the dataset
- `target` runs our real agent on the example's question
- `correctness` asks gpt-4o (the same Foundry model, acting as judge)
  whether the agent's answer matches the reference
- results land in a new "experiment" in the LangSmith UI, with every
  agent run fully traced

Note: the flaky weather tool can fail mid-eval. That's intentional --
watch how a failed run shows up inside an experiment.
"""

from dotenv import load_dotenv

load_dotenv()

from langsmith import Client  # noqa: E402

from ..agent.graph import graph  # noqa: E402
from ..agent.llm import get_llm  # noqa: E402
from .dataset import DATASET_NAME  # noqa: E402

JUDGE_PROMPT = """You are grading an AI agent's answer against a reference.

Question: {question}
Reference answer: {reference}
Agent's answer: {answer}

The agent's answer is CORRECT if it contains the same facts/numbers as the
reference (wording may differ; small rounding is fine). For weather questions,
matching the temperature and using it correctly is what matters.

Reply with exactly one word: CORRECT or INCORRECT."""


def target(inputs: dict) -> dict:
    """Run the real agent on one dataset example."""
    result = graph.invoke({"messages": [("user", inputs["question"])]})
    return {"answer": result["messages"][-1].content}


def correctness(inputs: dict, outputs: dict, reference_outputs: dict) -> bool:
    """LLM-as-judge: does the agent's answer match the reference?"""
    verdict = get_llm().invoke(
        JUDGE_PROMPT.format(
            question=inputs["question"],
            reference=reference_outputs["answer"],
            answer=outputs["answer"],
        )
    )
    return verdict.content.strip().upper().startswith("CORRECT")


def main() -> None:
    client = Client()
    results = client.evaluate(
        target,
        data=DATASET_NAME,
        evaluators=[correctness],
        experiment_prefix="baseline-gpt4o",
        max_concurrency=2,
    )
    print(f"\nexperiment: {results.experiment_name}")
    print("open LangSmith -> Datasets & Experiments to inspect it")


if __name__ == "__main__":
    main()
