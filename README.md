# DeepResearch Agent: Fullstack LangGraph Quickstart

This project demonstrates a fullstack application using a React frontend and a LangGraph-powered backend agent (the "DeepResearch Agent"). The agent is designed to perform comprehensive research on a user's query. It can dynamically generate search terms, query the web using configurable search providers (Google Search, Brave Search, or a self-hosted SearxNG instance), reflect on the results to identify knowledge gaps, and iteratively refine its search until it can provide a well-supported answer with citations. The Language Model (LLM) powering the agent's reasoning can also be configured to use powerful AI models (using Google models like Gemini by default when Google is the provider) or a custom OpenAI-compatible LLM endpoint. This application serves as an example of building research-augmented conversational AI with flexible backend configurations using LangGraph.

![DeepResearch Agent](./app.png)

## Features

- 💬 Fullstack application with a React frontend and LangGraph backend (DeepResearch Agent).
- 🧠 Powered by a LangGraph agent for advanced research and conversational AI.
- ⚙️ **Configurable Search Providers:** Choose between Google Search, Brave Search, or a self-hosted SearxNG instance.
- ⚙️ **Configurable LLM Providers:** Use Google AI models (e.g., Gemini models) or connect to any custom OpenAI-compatible LLM endpoint (e.g., local models via LM Studio, Ollama, or llama.cpp server).
- 🔍 Dynamic search query generation.
- 🌐 Integrated web research via the selected provider.
- 🤔 Reflective reasoning to identify knowledge gaps and refine searches.
- 📄 Generates answers with citations from gathered sources.
- 🔄 Hot-reloading for both frontend and backend development during development.

## Project Structure

The project is divided into two main directories:

-   `frontend/`: Contains the React application built with Vite.
-   `backend/`: Contains the LangGraph/FastAPI application, including the research agent logic.

## Getting Started: Development and Local Testing

Follow these steps to get the application running locally for development and testing.

**1. Prerequisites:**

-   Node.js and npm (or yarn/pnpm)
-   Python 3.8+
-   API Keys / Service URLs depending on your chosen providers (see Backend Configuration).

**2. Backend Configuration:**

The backend agent requires specific environment variables to be set based on your chosen Search and LLM providers.

1.  Navigate to the `backend/` directory.
2.  Create a file named `.env` by copying the `backend/.env.example` file.
3.  Open the `.env` file and configure the following variables as needed:

    *   `GEMINI_API_KEY="YOUR_ACTUAL_API_KEY"`
        *   **Required if** using "google" as the `LLM_PROVIDER` (for Google AI models like Gemini) or "google" as the `SEARCH_API_PROVIDER`.
        *   This key is used for Google AI models and the Google Search API (if `google_search` tool is used).

    *   `SEARCH_API_PROVIDER="google"`
        *   Specifies the search API provider.
        *   Options:
            *   `"google"`: (Default) Uses Google Search via the Gemini function calling. Requires `GEMINI_API_KEY`.
            *   `"brave"`: Uses the Brave Search API. Requires `SEARCH_API_KEY`.
            *   `"searxng"`: Uses a self-hosted or public SearxNG instance. Requires `SEARXNG_BASE_URL`.
        *   Example: `SEARCH_API_PROVIDER="brave"`

    *   `SEARCH_API_KEY=""`
        *   **Required if** `SEARCH_API_PROVIDER="brave"`.
        *   Your API key for Brave Search. You can obtain one from [Brave Search API website](https://brave.com/api/search).
        *   Example: `SEARCH_API_KEY="your_brave_api_subscription_token"`

    *   `SEARXNG_BASE_URL=""`
        *   **Required if** `SEARCH_API_PROVIDER="searxng"`.
        *   The base URL of your SearxNG instance.
        *   Example for a local instance: `SEARXNG_BASE_URL="http://localhost:8888"`

    *   `LLM_PROVIDER="google"`
        *   Specifies the Language Model provider for the agent's reasoning steps (query generation, reflection, answer finalization).
        *   Options:
            *   `"google"`: (Default) Uses Google AI models (e.g., Gemini models). Requires `GEMINI_API_KEY`. The specific models used for different tasks (query generation, reflection, answer) are defined in `backend/src/agent/configuration.py` and can be customized there if needed.
            *   `"custom"`: Uses a custom LLM that is compatible with the OpenAI API format. Requires `LLM_API_BASE_URL` and optionally `LLM_API_KEY` and `LLM_MODEL_NAME`.
            *   `"openai"`: Uses OpenAI models directly. Requires `LLM_API_KEY` (typically your OpenAI API key) and optionally `LLM_MODEL_NAME`. *(Note: While "openai" is an option, the primary focus for custom models is the "custom" provider for broader compatibility with self-hosted/alternative OpenAI-compatible endpoints).*
        *   Example: `LLM_PROVIDER="custom"`

    *   `LLM_API_BASE_URL=""`
        *   **Required if** `LLM_PROVIDER="custom"` or potentially `"openai"` if using a proxy/alternative endpoint.
        *   The base URL of your OpenAI-compatible LLM API.
        *   Example for a local LM Studio server: `LLM_API_BASE_URL="http://localhost:1234/v1"`

    *   `LLM_API_KEY=""`
        *   Optional, but often **required if** `LLM_PROVIDER="custom"` or `LLM_PROVIDER="openai"`.
        *   The API key for your custom LLM service or OpenAI. For many local LLMs, this might not be required, or you can use a placeholder value if the server expects one but doesn't validate it.
        *   Example: `LLM_API_KEY="your_custom_llm_api_key_or_openai_key"`

    *   `LLM_MODEL_NAME=""`
        *   Optional. Used if `LLM_PROVIDER="custom"` or `LLM_PROVIDER="openai"`.
        *   Specifies the model name your custom LLM server uses or the specific OpenAI model you want to use. If not provided, a default might be used by the backend (e.g., "gpt-3.5-turbo" for OpenAI, or a default specified in `ChatOpenAI` for "custom").
        *   Example for a local Llama model: `LLM_MODEL_NAME="Meta-Llama-3-8B-Instruct-GGUF"`
        *   Example for OpenAI: `LLM_MODEL_NAME="gpt-4-turbo"`

**3. Frontend Configuration (via UI):**

The frontend allows you to override or set some of these configurations dynamically through a Settings dialog.

*   Click the **Cog icon** (⚙️) in the application header to open the Settings dialog.
*   **Search API Provider:**
    *   Choose "Google", "Brave Search", or "SearXNG".
    *   If "Brave Search" is selected, an input field for "Brave API Key" will appear.
    *   If "SearXNG" is selected, an input field for "SearXNG Base URL" will appear.
*   **LLM Provider:**
    *   Choose "Google" or "Custom (OpenAI-compatible)".
    *   If "Custom (OpenAI-compatible)" is selected, input fields for "LLM API Base URL", "LLM API Key (Optional)", and "LLM Model Name (Optional)" will appear.
*   Settings are saved in your browser's `localStorage` and will be automatically sent to the backend with each new research request.

**Custom LLM Example (using LM Studio):**

If you are running a local LLM like LM Studio, which provides an OpenAI-compatible endpoint (e.g., at `http://localhost:1234/v1`):
1.  In the frontend Settings dialog:
    *   Set **LLM Provider** to: `Custom (OpenAI-compatible)`
    *   Set **LLM API Base URL** to: `http://localhost:1234/v1`
    *   Set **LLM API Key**: (Leave blank or enter any string if your LM Studio server doesn't require one)
    *   Set **LLM Model Name**: Enter the model identifier your LM Studio server uses (e.g., `lmstudio-community/Meta-Llama-3-8B-Instruct-GGUF`). You can usually find this in LM Studio's interface.
2.  Alternatively, you can set these in the `backend/.env` file:
    ```env
    LLM_PROVIDER="custom"
    LLM_API_BASE_URL="http://localhost:1234/v1"
    LLM_API_KEY="" # Or your key if needed
    LLM_MODEL_NAME="your-model-identifier-from-lm-studio"
    ```

**4. Install Dependencies:**

**Backend:**

```bash
cd backend
pip install .
# If you added new dependencies like langchain-openai, ensure they are in pyproject.toml
# and re-run pip install .
```

**Frontend:**

```bash
cd frontend
npm install
# If new dependencies like lucide-react were added, ensure they are in package.json
# and re-run npm install
```

**5. Run Development Servers:**

**Backend & Frontend:**

```bash
make dev
```
This will run the backend and frontend development servers. Open your browser and navigate to the frontend development server URL (e.g., `http://localhost:5173/app`).

_Alternatively, you can run the backend and frontend development servers separately. For the backend, open a terminal in the `backend/` directory and run `langgraph dev`. The backend API will be available at `http://127.0.0.1:2024`. It will also open a browser window to the LangGraph UI. For the frontend, open a terminal in the `frontend/` directory and run `npm run dev`. The frontend will be available at `http://localhost:5173`._

## How the Backend Agent Works (High-Level)

The core of the backend is a LangGraph agent defined in `backend/src/agent/graph.py`. It follows these steps:

![Agent Flow](./agent.png)

1.  **Generate Initial Queries:** Based on your input and configured LLM, it generates a set of initial search queries.
2.  **Web Research:** For each query, it uses the configured Search API Provider to find relevant web pages.
3.  **Reflection & Knowledge Gap Analysis:** The agent analyzes the search results to determine if the information is sufficient or if there are knowledge gaps. It uses the configured LLM for this reflection process.
4.  **Iterative Refinement:** If gaps are found or the information is insufficient, it generates follow-up queries and repeats the web research and reflection steps (up to a configured maximum number of loops).
5.  **Finalize Answer:** Once the research is deemed sufficient, the agent synthesizes the gathered information into a coherent answer, including citations from the web sources, using the configured LLM.

## Deployment

In production, the backend server serves the optimized static frontend build. LangGraph requires a Redis instance and a Postgres database. Redis is used as a pub-sub broker to enable streaming real time output from background runs. Postgres is used to store assistants, threads, runs, persist thread state and long term memory, and to manage the state of the background task queue with 'exactly once' semantics. For more details on how to deploy the backend server, take a look at the [LangGraph Documentation](https://langchain-ai.github.io/langgraph/concepts/deployment_options/). Below is an example of how to build a Docker image that includes the optimized frontend build and the backend server and run it via `docker-compose`.

_Note: For the docker-compose.yml example you need a LangSmith API key, you can get one from [LangSmith](https://smith.langchain.com/settings)._

_Note: If you are not running the docker-compose.yml example or exposing the backend server to the public internet, you update the `apiUrl` in the `frontend/src/App.tsx` file your host. Currently the `apiUrl` is set to `http://localhost:8123` for docker-compose or `http://localhost:2024` for development._

**1. Build the Docker Image:**

   Run the following command from the **project root directory**:
   ```bash
   docker build -t deepresearch-agent -f Dockerfile .
   ```
**2. Run the Production Server:**
   Ensure your `.env` file in the `backend/` directory is configured with your desired production settings for providers and keys. These will be used by the Docker container if not overridden in `docker-compose.yml` or its environment.

   ```bash
   # Example, assuming GEMINI_API_KEY is primary for this setup
   GEMINI_API_KEY=<your_gemini_api_key> LANGSMITH_API_KEY=<your_langsmith_api_key> docker-compose up
   # For more complex setups, you might need to pass more ENV variables to docker-compose
   # If using a different docker image name in docker-compose.yml, update it there too.
   ```

Open your browser and navigate to `http://localhost:8123/app/` to see the application. The API will be available at `http://localhost:8123`.

## Technologies Used

- [React](https://reactjs.org/) (with [Vite](https://vitejs.dev/)) - For the frontend user interface.
- [Tailwind CSS](https://tailwindcss.com/) - For styling.
- [Shadcn UI](https://ui.shadcn.com/) - For components.
- [LangGraph](https://github.com/langchain-ai/langgraph) - For building the backend research agent (DeepResearch Agent).
- Google AI Models (e.g., [Gemini](https://ai.google.dev/models/gemini)) - Default LLMs when using the Google provider for query generation, reflection, and answer synthesis.
- [Brave Search API](https://brave.com/api/search) - Alternative search provider.
- SearxNG - Alternative, self-hostable metasearch engine.
- OpenAI-compatible LLMs - Support for custom LLM endpoints.

## Manual Testing Checklist

This checklist can be used to manually verify the core new functionalities:

*   **TC1: Default (Google Search + Google LLM)**
    *   Action: Clear any settings in the UI (or localStorage). Run a query without opening/changing settings.
    *   Expected: Works as before, using Google Search and Google LLM. Observe typical Google-style search results in the agent's thoughts (if visible) and Gemini-like responses.
*   **TC2: Brave Search + Google LLM**
    *   Action: In Settings, select "Brave Search" as Search API Provider. Enter a valid Brave Search API key. Keep LLM Provider as "Google". Save settings. Run a query.
    *   Expected: The agent should complete the research. It's hard to programmatically verify Brave results without inspecting backend logs or unique Brave result characteristics, but the agent should not fail due to search issues.
*   **TC3: SearxNG + Google LLM**
    *   Action: In Settings, select "SearXNG" as Search API Provider. Enter a valid URL for a working SearxNG instance. Keep LLM Provider as "Google". Save settings. Run a query.
    *   Expected: The agent should complete the research using SearxNG.
*   **TC4: Google Search + Custom LLM (OpenAI-compatible)**
    *   Action: In Settings, keep "Google" as Search API Provider. Select "Custom (OpenAI-compatible)" as LLM Provider. Enter a valid API Base URL for an OpenAI-compatible LLM (e.g., a local LM Studio endpoint like `http://localhost:1234/v1`). Enter the correct model name if required by your local LLM. Save settings. Run a query.
    *   Expected: Agent uses the custom LLM for generation, reflection, and answer. Responses might differ in style from Gemini. Check backend logs if your custom LLM server shows incoming requests.
*   **TC5: Brave Search + Custom LLM**
    *   Action: Combine settings from TC2 (for Brave) and TC4 (for Custom LLM). Run a query.
    *   Expected: Agent uses Brave for search and the Custom LLM for all text generation tasks.
*   **TC6: Invalid Brave API Key**
    *   Action: Configure Brave Search provider + an obviously invalid/fake API key. Run a query.
    *   Expected: The agent should fail gracefully. The UI should ideally show an error message, or the process should terminate with a clear error notification. The backend should log an authentication error from Brave.
*   **TC7: Invalid SearxNG URL**
    *   Action: Configure SearxNG provider + an invalid or unreachable URL (e.g., `http://localhost:1235/nonexistent`). Run a query.
    *   Expected: Graceful failure or error message. Backend logs should indicate a connection or resolution error for the SearxNG URL.
*   **TC8: Invalid Custom LLM URL**
    *   Action: Configure Custom LLM provider + an invalid or unreachable API Base URL. Run a query.
    *   Expected: Graceful failure or error message. Backend logs should indicate errors connecting to the LLM endpoint.

## License

This project is licensed under the Apache License 2.0. See the [LICENSE](LICENSE) file for details.