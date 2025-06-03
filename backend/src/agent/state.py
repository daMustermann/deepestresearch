from __future__ import annotations

from dataclasses import dataclass, field
from typing import TypedDict, Optional # Added Optional

from langgraph.graph import add_messages
from typing_extensions import Annotated

import operator

class OverallState(TypedDict, total=False): # Set total=False to make all fields optional by default
    messages: Annotated[list, add_messages]
    search_query: Annotated[list, operator.add]
    web_research_result: Annotated[list, operator.add]
    sources_gathered: Annotated[list, operator.add]
    initial_search_query_count: int # Will be set by generate_query or from input
    max_research_loops: int # Will be set by reflection/evaluate_research or from input
    research_loop_count: int # Initialized/updated in reflection
    reasoning_model: str # From input

    # New fields for UI-driven configuration - these are truly optional
    llm_provider: Optional[str]
    llm_api_base_url: Optional[str]
    llm_api_key: Optional[str]
    llm_model_name: Optional[str]
    search_api_provider: Optional[str]
    search_api_key: Optional[str]
    searxng_base_url: Optional[str]

class ReflectionState(TypedDict, total=False): # Set total=False
    is_sufficient: bool
    knowledge_gap: str
    follow_up_queries: Annotated[list, operator.add]
    research_loop_count: int
    number_of_ran_queries: int

class Query(TypedDict): # Assuming these are always fully populated when created
    query: str
    rationale: str

class QueryGenerationState(TypedDict, total=False): # Set total=False
    query_list: list[Query]

class WebSearchState(TypedDict, total=False): # Set total=False
    search_query: str
    id: str # This 'id' seems to be an index for parallel searches

@dataclass(kw_only=True)
class SearchStateOutput: # This is not directly part of LangGraph state, seems like a data structure
    running_summary: Optional[str] = field(default=None)
