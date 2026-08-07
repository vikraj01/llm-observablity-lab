"""Run an experiment over the golden dataset in Langfuse.

Usage:
    uv run python -m src.obs_langfuse.evaluate

Same agent, same judge model, same cases as Phase 3 -- but note one
upgrade over our LangSmith evaluator: the judge now returns a comment
explaining its verdict, which Langfuse shows next to the score.
"""

from dotenv import load_dotenv

load_dotenv()

from langfuse import Evaluation, get_client  # noqa: E402
from langfuse.langchain import CallbackHandler  # noqa: E402

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

First line: exactly CORRECT or INCORRECT.
Second line: one short sentence explaining why."""


def task(*, item, **kwargs):
    """Run the real agent on one dataset item (fully traced via callback)."""
    handler = CallbackHandler()
    result = graph.invoke(
        {"messages": [("user", item.input["question"])]},
        config={"callbacks": [handler]},
    )
    return result["messages"][-1].content


def correctness(*, input, output, expected_output, **kwargs):
    """LLM-as-judge with an explanation comment."""
    verdict = get_llm().invoke(
        JUDGE_PROMPT.format(
            question=input["question"],
            reference=expected_output["answer"],
            answer=output,
        )
    )
    lines = verdict.content.strip().splitlines()
    is_correct = lines[0].strip().upper().startswith("CORRECT")
    comment = lines[1].strip() if len(lines) > 1 else ""
    return Evaluation(name="correctness", value=1.0 if is_correct else 0.0, comment=comment)


def main() -> None:
    langfuse = get_client()
    dataset = langfuse.get_dataset(DATASET_NAME)
    result = dataset.run_experiment(
        name="baseline-gpt4o",
        description="Same setup as the LangSmith Phase 3 experiment",
        task=task,
        evaluators=[correctness],
    )
    langfuse.flush()
    print(f"\nexperiment finished: {len(result.item_results)} items")
    print("open Langfuse -> Datasets -> llm-obs-lab-golden -> Runs to inspect")


if __name__ == "__main__":
    main()
