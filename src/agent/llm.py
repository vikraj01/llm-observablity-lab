
import os
from functools import lru_cache

from langchain_openai import ChatOpenAI, OpenAIEmbeddings


@lru_cache(maxsize=1)
def get_llm() -> ChatOpenAI:
    return ChatOpenAI(
        model=os.environ["LLM_CHAT_MODEL"],
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["LLM_API_KEY"],
        temperature=0,
    )


@lru_cache(maxsize=1)
def get_embeddings() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(
        model=os.environ["LLM_EMBEDDING_MODEL"],
        base_url=os.environ["LLM_BASE_URL"],
        api_key=os.environ["LLM_API_KEY"],
    )
