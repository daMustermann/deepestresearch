import os
from pydantic import BaseModel, Field
from typing import Any, Optional

from langchain_core.runnables import RunnableConfig


class Configuration(BaseModel):
    """The configuration for the agent."""

    query_generator_model: str = Field(
        default="gemini-2.0-flash",
        metadata={
            "description": "The name of the language model to use for the agent's query generation."
        },
    )

    reflection_model: str = Field(
        default="gemini-2.5-flash-preview-04-17",
        metadata={
            "description": "The name of the language model to use for the agent's reflection."
        },
    )

    answer_model: str = Field(
        default="gemini-2.5-pro-preview-05-06",
        metadata={
            "description": "The name of the language model to use for the agent's answer."
        },
    )

    search_api_provider: str = Field(
        default="google",
        metadata={"description": "The search API provider to use (e.g., 'google', 'searxng')."},
    )
    search_api_key: Optional[str] = Field(
        default=None, metadata={"description": "The API key for the search provider."}
    )
    searxng_base_url: Optional[str] = Field(
        default=None, metadata={"description": "The base URL for SearXNG instances."}
    )

    llm_provider: str = Field(
        default="google",
        metadata={"description": "The LLM provider to use (e.g., 'google', 'openai')."},
    )
    llm_api_base_url: Optional[str] = Field(
        default=None, metadata={"description": "The base URL for custom LLM APIs."}
    )
    llm_api_key: Optional[str] = Field(
        default=None, metadata={"description": "The API key for the LLM provider."}
    )
    llm_model_name: Optional[str] = Field(
        default=None, metadata={"description": "The specific model name for custom LLMs."}
    )

    number_of_initial_queries: int = Field(
        default=3,
        metadata={"description": "The number of initial search queries to generate."},
    )

    max_research_loops: int = Field(
        default=2,
        metadata={"description": "The maximum number of research loops to perform."},
    )

    @classmethod
    def from_runnable_config(
        cls, config: Optional[RunnableConfig] = None
    ) -> "Configuration":
        """Create a Configuration instance from a RunnableConfig."""
        configurable = (
            config["configurable"] if config and "configurable" in config else {}
        )

        # Get raw values from environment or config
        raw_values: dict[str, Any] = {}
        for name in cls.model_fields.keys():
            env_var_name = name.upper()
            value = os.environ.get(env_var_name, configurable.get(name))
            raw_values[name] = value

        # Filter out None values, unless the field is explicitly Optional
        values = {}
        for k, v in raw_values.items():
            if v is not None:
                values[k] = v
            # For optional fields, we still want to include them if they are explicitly set to None
            # or if they are not present in the environment/config (which results in v being None)
            # and the field definition allows None.
            elif cls.model_fields[k].is_required() is False:
                values[k] = None


        return cls(**values)
