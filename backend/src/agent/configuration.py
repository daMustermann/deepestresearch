import os
from pydantic import BaseModel, Field
from typing import Any, Optional, Dict

from langchain_core.runnables import RunnableConfig

class Configuration(BaseModel):
    """The configuration for the agent."""

    query_generator_model: str = Field(
        default="gemini-2.0-flash",
        description="The name of the language model to use for the agent's query generation."
    )

    reflection_model: str = Field(
        default="gemini-2.5-flash-preview-04-17",
        description="The name of the language model to use for the agent's reflection."
    )

    answer_model: str = Field(
        default="gemini-2.5-pro-preview-05-06",
        description="The name of the language model to use for the agent's answer."
    )

    search_api_provider: str = Field(
        default="google",
        description="The search API provider to use (e.g., 'google', 'searxng')."
    )
    search_api_key: Optional[str] = Field(
        default=None, description="The API key for the search provider."
    )
    searxng_base_url: Optional[str] = Field(
        default=None, description="The base URL for SearXNG instances."
    )

    llm_provider: str = Field(
        default="google",
        description="The LLM provider to use (e.g., 'google', 'openai')."
    )
    llm_api_base_url: Optional[str] = Field(
        default=None, description="The base URL for custom LLM APIs."
    )
    llm_api_key: Optional[str] = Field(
        default=None, description="The API key for the LLM provider."
    )
    llm_model_name: Optional[str] = Field(
        default=None, description="The specific model name for custom LLMs."
    )

    number_of_initial_queries: int = Field(
        default=3,
        description="The number of initial search queries to generate."
    )

    max_research_loops: int = Field(
        default=2,
        description="The maximum number of research loops to perform."
    )

    @classmethod
    def from_runnable_config(
        cls, 
        config: Optional[RunnableConfig] = None,
        state_config_override: Optional[Dict[str, Any]] = None
    ) -> "Configuration":
        """
        Create a Configuration instance.
        Priority:
        1. state_config_override (values passed explicitly from AgentState)
        2. config["configurable"] (values from RunnableConfig, typically LangGraph internal)
        3. Environment variables
        4. Pydantic defaults
        """
        lg_configurable = ( # LangGraph's internal configurable
            config["configurable"] if config and "configurable" in config else {}
        )
        state_override = state_config_override if state_config_override is not None else {}

        print(f"--- [DEBUG] from_runnable_config ---")
        print(f"--- [DEBUG] state_config_override received: {state_override}")
        print(f"--- [DEBUG] LangGraph's internal config object: {config}")
        print(f"--- [DEBUG] LangGraph's internal 'configurable' dict: {lg_configurable}")

        raw_values: dict[str, Any] = {}
        
        for name in cls.model_fields.keys():
            value: Any = None
            source: str = "Pydantic default"

            # 1. Check state_config_override
            if name in state_override and state_override[name] is not None:
                value = state_override[name]
                source = "state_config_override"
            else:
                # 2. Check LangGraph's internal configurable (less likely to contain our UI settings)
                # We've seen this doesn't contain UI settings, but keeping for completeness of original logic.
                # This is unlikely to be useful for UI-driven config.
                # if name in lg_configurable and lg_configurable[name] is not None:
                #     value = lg_configurable[name]
                #     source = "LangGraph internal configurable"
                # else:
                # 3. Check environment variables
                env_var_name = name.upper()
                env_value = os.environ.get(env_var_name)
                if env_value is not None:
                    value = env_value
                    source = f"environment variable ({env_var_name})"
            
            print(f"--- [DEBUG] For '{name}': resolved value '{value}' from '{source}'")
            raw_values[name] = value # Value can be None here if not found anywhere yet

        init_kwargs: dict[str, Any] = {}
        for name, raw_value in raw_values.items():
            if raw_value is not None: 
                init_kwargs[name] = raw_value
        
        print(f"--- [DEBUG] Final init_kwargs for Configuration: {init_kwargs}")
        
        instance = cls(**init_kwargs)
        print(f"--- [DEBUG] Created Configuration instance (model_dump): {instance.model_dump()}")
        print(f"--- [DEBUG] --- end from_runnable_config ---")
        return instance
