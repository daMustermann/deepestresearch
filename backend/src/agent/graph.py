import os

from agent.tools_and_schemas import SearchQueryList, Reflection
from dotenv import load_dotenv
from langchain_core.messages import AIMessage
from langgraph.types import Send
from langgraph.graph import StateGraph
from langgraph.graph import START, END
from langchain_core.runnables import RunnableConfig
from google.genai import Client # type: ignore
from pydantic import SecretStr # Import SecretStr

from agent.state import (
    OverallState,
)
from agent.configuration import Configuration
from typing import Optional, Dict, Any, List, Union

from langchain_openai import ChatOpenAI
from agent.search_tools import brave_search, searxng_search
from agent.prompts import (
    get_current_date,
    query_writer_instructions,
    web_searcher_instructions,
    reflection_instructions,
    answer_instructions,
)
from langchain_google_genai import ChatGoogleGenerativeAI
from agent.utils import (
    get_citations,
    get_research_topic,
    insert_citation_markers,
    resolve_urls,
)

load_dotenv(override=True)

_initial_app_config_for_checks = Configuration.from_runnable_config()
gemini_api_key_env = os.getenv("GEMINI_API_KEY")

if _initial_app_config_for_checks.llm_provider == "google" and not gemini_api_key_env:
    raise ValueError(
        "GEMINI_API_KEY is not set in .env, but Google is the configured LLM provider."
    )

genai_client: Optional[Client] = None
if gemini_api_key_env:
    genai_client = Client(api_key=gemini_api_key_env)
elif _initial_app_config_for_checks.search_api_provider == "google" and _initial_app_config_for_checks.llm_provider != "google":
    raise ValueError(
        "GEMINI_API_KEY is not set in .env, but Google is the configured Search API provider."
    )

def _get_config_from_state(state: OverallState) -> Dict[str, Any]:
    cfg_keys = [
        "llm_provider", "llm_api_base_url", "llm_api_key", "llm_model_name",
        "search_api_provider", "search_api_key", "searxng_base_url",
        "number_of_initial_queries", "max_research_loops"
    ]
    state_cfg: Dict[str, Any] = {}
    for key in cfg_keys:
        value = state.get(key)
        if value is not None:
            state_cfg[key] = value
    return state_cfg

# Nodes
def generate_query(state: OverallState, config: RunnableConfig) -> dict:
    state_cfg_override = _get_config_from_state(state)
    app_config = Configuration.from_runnable_config(config, state_config_override=state_cfg_override)

    initial_query_count = state.get("initial_search_query_count")
    if initial_query_count is None:
        initial_query_count = app_config.number_of_initial_queries

    llm_api_key_to_use: Optional[SecretStr] = None
    if app_config.llm_api_key:
        llm_api_key_to_use = SecretStr(app_config.llm_api_key)
    
    openai_api_key_env: Optional[SecretStr] = None
    openai_env_val = os.getenv("OPENAI_API_KEY")
    if openai_env_val:
        openai_api_key_env = SecretStr(openai_env_val)

    llm: Union[ChatOpenAI, ChatGoogleGenerativeAI]
    if app_config.llm_provider == "custom":
        if not app_config.llm_api_base_url:
            raise ValueError("LLM_API_BASE_URL must be set for custom LLM provider.")
        llm = ChatOpenAI(
            model=app_config.llm_model_name or "gpt-3.5-turbo",
            base_url=app_config.llm_api_base_url,
            api_key=llm_api_key_to_use,
            temperature=1.0, max_retries=2,
        )
    elif app_config.llm_provider == "openai":
        llm = ChatOpenAI(
            model=app_config.llm_model_name or "gpt-3.5-turbo",
            api_key=llm_api_key_to_use or openai_api_key_env,
            temperature=1.0, max_retries=2,
        )
    else: # Default to google
        llm = ChatGoogleGenerativeAI(
            model=app_config.query_generator_model,
            temperature=1.0, max_retries=2,
            api_key=os.getenv("GEMINI_API_KEY") if app_config.llm_provider == "google" else None,
        )
    
    structured_llm_method_kwargs = {}
    if isinstance(llm, ChatOpenAI):
        # Use json_mode for ChatOpenAI to potentially avoid tool_choice object issues
        structured_llm_method_kwargs["method"] = "json_mode" 
        # Ensure the model used supports JSON mode. Most recent OpenAI models do.
        # For JSON mode to work, prompts might need to explicitly ask for JSON output.
        # LangChain's with_structured_output(method="json_mode") typically handles this.

    structured_llm = llm.with_structured_output(SearchQueryList, **structured_llm_method_kwargs)

    current_date = get_current_date()
    messages = state.get("messages", [])
    formatted_prompt = query_writer_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(messages),
        number_queries=initial_query_count,
    )
    result: SearchQueryList = structured_llm.invoke(formatted_prompt) # type: ignore 
    return {"query_list": result.query, "initial_search_query_count": initial_query_count}

def continue_to_web_research(state: OverallState, config: RunnableConfig) -> List[Send]:
    query_list = state.get("query_list", [])
    sends = []
    for idx, search_query_item in enumerate(query_list):
        actual_query_str = search_query_item.get("query") if isinstance(search_query_item, dict) else str(search_query_item)
        if actual_query_str:
             sends.append(Send("web_research", {"search_query": actual_query_str, "id": str(idx)}))
    return sends

def web_research(state: OverallState, config: RunnableConfig) -> dict:
    state_cfg_override = _get_config_from_state(state)
    app_config = Configuration.from_runnable_config(config, state_config_override=state_cfg_override)

    web_research_outputs = []
    sources_gathered_outputs = []
    
    current_search_query = state.get("search_query")
    if not isinstance(current_search_query, str) or not current_search_query:
        return {"sources_gathered": [], "search_query": [], "web_research_result": ["Error: Invalid or no search query provided."]}

    search_query_for_output = [current_search_query]

    if app_config.search_api_provider == "brave":
        if not app_config.search_api_key:
            raise ValueError("SEARCH_API_KEY must be set for Brave Search.")
        search_results_obj = brave_search(current_search_query, app_config.search_api_key)
    elif app_config.search_api_provider == "searxng":
        if not app_config.searxng_base_url:
            raise ValueError("SEARXNG_BASE_URL must be set for SearxNG.")
        search_results_obj = searxng_search(current_search_query, app_config.searxng_base_url)
    elif app_config.search_api_provider == "google":
        if not genai_client:
             raise ValueError("Google GenAI client not initialized. Check GEMINI_API_KEY.")
        formatted_prompt = web_searcher_instructions.format(
            current_date=get_current_date(),
            research_topic=current_search_query,
        )
        response = genai_client.models.generate_content(
            model=app_config.query_generator_model, # This is for Google Search, not the main LLM
            contents=formatted_prompt,
            config={"tools": [{"google_search": {}}], "temperature": 0,},
        )
        
        grounding_chunks = None
        if response.candidates and response.candidates[0].grounding_metadata: # type: ignore
            grounding_chunks = response.candidates[0].grounding_metadata.grounding_chunks # type: ignore
        
        if not grounding_chunks:
            web_research_outputs.append(f"No results or grounding metadata from Google Search for: {current_search_query}")
            search_results_obj = None
        else:
            resolved_urls = resolve_urls(grounding_chunks, state.get("id", "0"))
            citations = get_citations(response, resolved_urls) # type: ignore
            modified_text = insert_citation_markers(response.text or "", citations) # type: ignore
            current_sources_gathered = [item for citation in citations for item in citation["segments"]]
            web_research_outputs.append(modified_text)
            sources_gathered_outputs.extend(current_sources_gathered)
            search_results_obj = None
    else:
        raise ValueError(f"Unsupported search API provider: {app_config.search_api_provider}")

    if app_config.search_api_provider != "google" and search_results_obj and search_results_obj.results:
        combined_snippets = []
        for i, res_item in enumerate(search_results_obj.results):
            combined_snippets.append(f"[{i+1}] {res_item.title}\n{res_item.snippet}\nURL: {res_item.url}")
            sources_gathered_outputs.append({
                "id": f"{state.get('id', '0')}_{i}", "title": res_item.title, "url": res_item.url, "value": res_item.url,
                "short_url": res_item.url, "segments": [{"text": res_item.snippet or "", "url": res_item.url, "title": res_item.title }]
            })
        web_research_outputs.append("\n\n---\n\n".join(combined_snippets))
    elif app_config.search_api_provider != "google" and (not search_results_obj or not search_results_obj.results):
        web_research_outputs.append(f"No results found or error in search for: {current_search_query}")

    return {
        "sources_gathered": sources_gathered_outputs,
        "search_query": search_query_for_output,
        "web_research_result": web_research_outputs,
    }

def reflection(state: OverallState, config: RunnableConfig) -> dict:
    state_cfg_override = _get_config_from_state(state)
    app_config = Configuration.from_runnable_config(config, state_config_override=state_cfg_override)
    
    current_research_loop_count = state.get("research_loop_count", 0) + 1
    reasoning_model_name_from_state = state.get("reasoning_model")
    llm_model_name_from_settings = app_config.llm_model_name

    effective_reflection_model = app_config.reflection_model
    if app_config.llm_provider in ["custom", "openai"]:
        if llm_model_name_from_settings: # Prioritize model from settings for custom/openai
            effective_reflection_model = llm_model_name_from_settings
    elif reasoning_model_name_from_state and app_config.llm_provider == "google":
        effective_reflection_model = reasoning_model_name_from_state


    llm_api_key_to_use: Optional[SecretStr] = None
    if app_config.llm_api_key:
        llm_api_key_to_use = SecretStr(app_config.llm_api_key)
    
    openai_api_key_env: Optional[SecretStr] = None
    openai_env_val = os.getenv("OPENAI_API_KEY")
    if openai_env_val:
        openai_api_key_env = SecretStr(openai_env_val)

    current_date = get_current_date()
    messages = state.get("messages", [])
    web_results = state.get("web_research_result", [])
    formatted_prompt = reflection_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(messages),
        summaries="\n\n---\n\n".join(web_results),
    )

    llm: Union[ChatOpenAI, ChatGoogleGenerativeAI]
    if app_config.llm_provider == "custom":
        if not app_config.llm_api_base_url:
            raise ValueError("LLM_API_BASE_URL must be set for custom LLM provider.")
        llm = ChatOpenAI(
            model=effective_reflection_model,
            base_url=app_config.llm_api_base_url,
            api_key=llm_api_key_to_use,
            temperature=1.0, max_retries=2,
        )
    elif app_config.llm_provider == "openai":
        llm = ChatOpenAI(
            model=effective_reflection_model,
            api_key=llm_api_key_to_use or openai_api_key_env,
            temperature=1.0, max_retries=2,
        )
    else: # Default to google
        llm = ChatGoogleGenerativeAI(
            model=effective_reflection_model,
            temperature=1.0, max_retries=2,
            api_key=os.getenv("GEMINI_API_KEY") if app_config.llm_provider == "google" else None,
        )

    structured_llm_method_kwargs = {}
    if isinstance(llm, ChatOpenAI):
        structured_llm_method_kwargs["method"] = "json_mode"

    structured_llm = llm.with_structured_output(Reflection, **structured_llm_method_kwargs)
    result: Reflection = structured_llm.invoke(formatted_prompt) # type: ignore

    new_query_list = []
    if result.follow_up_queries:
        for fq_text in result.follow_up_queries:
            if isinstance(fq_text, str) and fq_text.strip():
                new_query_list.append({"query": fq_text, "rationale": "Follow-up query from reflection."})
            elif isinstance(fq_text, dict) and fq_text.get("query"):
                 new_query_list.append(fq_text)

    return {
        "is_sufficient": result.is_sufficient,
        "knowledge_gap": result.knowledge_gap,
        "follow_up_queries": result.follow_up_queries,
        "query_list": new_query_list,
        "research_loop_count": current_research_loop_count,
        "number_of_ran_queries": len(state.get("search_query", [])),
    }

def evaluate_research(state: OverallState, config: RunnableConfig) -> Union[str, List[Send]]:
    state_cfg_override = _get_config_from_state(state)
    app_config = Configuration.from_runnable_config(config, state_config_override=state_cfg_override)

    max_loops = state.get("max_research_loops")
    if max_loops is None:
        max_loops = app_config.max_research_loops

    if state.get("is_sufficient") or state.get("research_loop_count", 0) >= max_loops:
        return "finalize_answer"
    else:
        follow_up_queries_from_reflection = state.get("follow_up_queries", [])
        number_ran = state.get("number_of_ran_queries", 0)
        sends = []

        for idx, fq_text in enumerate(follow_up_queries_from_reflection):
            actual_query_str = fq_text
            if isinstance(fq_text, dict) and fq_text.get("query"): # Should be list of str from Reflection schema
                actual_query_str = fq_text.get("query")
            
            if isinstance(actual_query_str, str) and actual_query_str.strip():
                payload = { "search_query": actual_query_str, "id": str(number_ran + idx) }
                sends.append(Send("web_research", payload))

        if not sends:
            return "finalize_answer"
        return sends

def finalize_answer(state: OverallState, config: RunnableConfig) -> dict:
    state_cfg_override = _get_config_from_state(state)
    app_config = Configuration.from_runnable_config(config, state_config_override=state_cfg_override)

    reasoning_model_name_from_state = state.get("reasoning_model")
    llm_model_name_from_settings = app_config.llm_model_name

    effective_answer_model = app_config.answer_model
    if app_config.llm_provider in ["custom", "openai"]:
        if llm_model_name_from_settings:
            effective_answer_model = llm_model_name_from_settings
    elif reasoning_model_name_from_state and app_config.llm_provider == "google":
         effective_answer_model = reasoning_model_name_from_state

    llm_api_key_to_use: Optional[SecretStr] = None
    if app_config.llm_api_key:
        llm_api_key_to_use = SecretStr(app_config.llm_api_key)
        
    openai_api_key_env: Optional[SecretStr] = None
    openai_env_val = os.getenv("OPENAI_API_KEY")
    if openai_env_val:
        openai_api_key_env = SecretStr(openai_env_val)

    current_date = get_current_date()
    messages = state.get("messages", [])
    web_results = state.get("web_research_result", [])
    formatted_prompt = answer_instructions.format(
        current_date=current_date,
        research_topic=get_research_topic(messages),
        summaries="\n---\n\n".join(web_results),
    )

    llm: Union[ChatOpenAI, ChatGoogleGenerativeAI]
    if app_config.llm_provider == "custom":
        if not app_config.llm_api_base_url:
            raise ValueError("LLM_API_BASE_URL must be set for custom LLM provider.")
        llm = ChatOpenAI(
            model=effective_answer_model,
            base_url=app_config.llm_api_base_url,
            api_key=llm_api_key_to_use,
            temperature=0, max_retries=2,
        )
    elif app_config.llm_provider == "openai":
        llm = ChatOpenAI(
            model=effective_answer_model,
            api_key=llm_api_key_to_use or openai_api_key_env,
            temperature=0, max_retries=2,
        )
    else: # Default to google
        llm = ChatGoogleGenerativeAI(
            model=effective_answer_model,
            temperature=0, max_retries=2,
            api_key=os.getenv("GEMINI_API_KEY") if app_config.llm_provider == "google" else None,
        )
    result = llm.invoke(formatted_prompt)
    
    final_content = result.content
    if not isinstance(final_content, str):
        final_content = str(final_content)

    unique_sources = []
    sources_gathered = state.get("sources_gathered", [])
    for source in sources_gathered:
        short_url = source.get("short_url")
        original_url = source.get("value")
        if short_url and original_url and short_url in final_content:
            final_content = final_content.replace(short_url, original_url)
            if source not in unique_sources:
                 unique_sources.append(source)
        elif original_url and original_url in final_content: # type: ignore
            if source not in unique_sources:
                 unique_sources.append(source)

    return {
        "messages": [AIMessage(content=final_content)],
        "sources_gathered": unique_sources,
    }

builder = StateGraph(OverallState, config_schema=RunnableConfig)

builder.add_node("generate_query", generate_query)
builder.add_node("web_research", web_research)
builder.add_node("reflection", reflection)
builder.add_node("finalize_answer", finalize_answer)

builder.add_edge(START, "generate_query")
builder.add_conditional_edges(
    "generate_query", 
    continue_to_web_research, # type: ignore
)
builder.add_edge("web_research", "reflection")
builder.add_conditional_edges(
    "reflection",
    evaluate_research # type: ignore
)
builder.add_edge("finalize_answer", END)

graph = builder.compile(checkpointer=None, name="pro-search-agent")
