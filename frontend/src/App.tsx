import { useStream } from "@langchain/langgraph-sdk/react";
import type { Message } from "@langchain/langgraph-sdk";
import { useState, useEffect, useRef, useCallback } from "react";
import { ProcessedEvent } from "@/components/ActivityTimeline";

// Definiert die Struktur für eine Quelle aus der Web-Recherche.
interface Source {
label: string;
// Hier könnten weitere Eigenschaften stehen, falls bekannt.
}

// Definiert die Struktur für Ereignisse, die vom Stream verarbeitet werden.
interface StreamEvent {
generate_query?: { query_list: string[] };
web_research?: { sources_gathered?: Source[] };
reflection?: { is_sufficient: boolean; follow_up_queries: string[] };
finalize_answer?: Record<string, unknown>; // Oder ein spezifischerer Typ, falls bekannt
}

import { WelcomeScreen } from "./components/WelcomeScreen";
import { ChatMessagesView } from "./components/ChatMessagesView";
import SettingsDialog from "./components/SettingsDialog"; // Import SettingsDialog
import { Button } from "./components/ui/button"; // Import Button
import { Cog } from "lucide-react"; // Import an icon for the button

// Define the input type for the stream, matching backend's OverallState for config
interface StreamInput {
  messages: Message[];
  reasoning_model: string; // Model selected in UI for the run (e.g. "gemini-1.5-flash")
  
  // Configuration fields from UI settings, matching OverallState and Configuration model
  number_of_initial_queries?: number; // Renamed from initial_search_query_count
  max_research_loops?: number;

  llm_provider?: string;
  llm_api_base_url?: string;
  llm_api_key?: string;
  llm_model_name?: string; // Specific model name from settings (e.g. "gpt-4o")
  search_api_provider?: string;
  search_api_key?: string;
  searxng_base_url?: string;

  [key: string]: unknown; // Index signature to satisfy Record<string, unknown> constraint and for assignIfDefined
}

export default function App() {
  const [processedEventsTimeline, setProcessedEventsTimeline] = useState<
    ProcessedEvent[]
  >([]);
  const [historicalActivities, setHistoricalActivities] = useState<
    Record<string, ProcessedEvent[]>
  >({});
  const [isSettingsDialogOpen, setIsSettingsDialogOpen] = useState(false); // State for dialog visibility
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const hasFinalizeEventOccurredRef = useRef(false);

  const thread = useStream<StreamInput>({ // Use the new StreamInput type
    apiUrl: import.meta.env.DEV
      ? "http://localhost:2024"
      : "http://localhost:8123",
    assistantId: "agent",
    messagesKey: "messages",
    onFinish: (event: unknown) => {
      console.log(event);
    },
    onUpdateEvent: (event: StreamEvent) => {
      let processedEvent: ProcessedEvent | null = null;
      if (event.generate_query) {
        processedEvent = {
          title: "Generating Search Queries",
          data: event.generate_query.query_list.join(", "),
        };
      } else if (event.web_research) {
        const sources = event.web_research.sources_gathered || [];
        const numSources = sources.length;
        const uniqueLabels = [
          ...new Set(sources.map((s: Source) => s.label).filter(Boolean)),
        ];
        const exampleLabels = uniqueLabels.slice(0, 3).join(", ");
        processedEvent = {
          title: "Web Research",
          data: `Gathered ${numSources} sources. Related to: ${
            exampleLabels || "N/A"
          }.`,
        };
      } else if (event.reflection) {
        processedEvent = {
          title: "Reflection",
          data: event.reflection.is_sufficient
            ? "Search successful, generating final answer."
            : `Need more information, searching for ${event.reflection.follow_up_queries.join(
                ", "
              )}`,
        };
      } else if (event.finalize_answer) {
        processedEvent = {
          title: "Finalizing Answer",
          data: "Composing and presenting the final answer.",
        };
        hasFinalizeEventOccurredRef.current = true;
      }
      if (processedEvent) {
        setProcessedEventsTimeline((prevEvents) => [
          ...prevEvents,
          processedEvent!,
        ]);
      }
    },
  });

  useEffect(() => {
    if (scrollAreaRef.current) {
      const scrollViewport = scrollAreaRef.current.querySelector(
        "[data-radix-scroll-area-viewport]"
      );
      if (scrollViewport) {
        scrollViewport.scrollTop = scrollViewport.scrollHeight;
      }
    }
  }, [thread.messages]);

  useEffect(() => {
    if (
      hasFinalizeEventOccurredRef.current &&
      !thread.isLoading &&
      thread.messages.length > 0
    ) {
      const lastMessage = thread.messages[thread.messages.length - 1];
      if (lastMessage && lastMessage.type === "ai" && lastMessage.id) {
        setHistoricalActivities((prev) => ({
          ...prev,
          [lastMessage.id!]: [...processedEventsTimeline],
        }));
      }
      hasFinalizeEventOccurredRef.current = false;
    }
  }, [thread.messages, thread.isLoading, processedEventsTimeline]);

  const handleSubmit = useCallback(
    (submittedInputValue: string, effort: string, model: string) => {
      if (!submittedInputValue.trim()) return;
      setProcessedEventsTimeline([]);
      hasFinalizeEventOccurredRef.current = false;

      let numQueries = 0; 
      let maxLoops = 0; 
      switch (effort) {
        case "low":
          numQueries = 1;
          maxLoops = 1;
          break;
        case "medium":
          numQueries = 3;
          maxLoops = 3;
          break;
        case "high":
          numQueries = 5;
          maxLoops = 10;
          break;
      }

      const newMessages: Message[] = [
        ...(thread.messages || []),
        {
          type: "human",
          content: submittedInputValue,
          id: Date.now().toString(),
        },
      ];

      const payload: StreamInput = {
        messages: newMessages,
        number_of_initial_queries: numQueries,
        max_research_loops: maxLoops,
        reasoning_model: model,
      };

      const settingsString = localStorage.getItem('appSettings');
      if (settingsString) {
        try {
          const parsedSettings = JSON.parse(settingsString);

          const assignIfDefined = (targetKey: keyof StreamInput, value: string | number | boolean | undefined | null) => {
            if (value !== undefined && value !== null && value !== '') {
              payload[targetKey] = value; // Removed @ts-expect-error
            }
          };

          assignIfDefined('search_api_provider', parsedSettings.searchApiProvider);
          assignIfDefined('search_api_key', parsedSettings.searchApiKey);
          assignIfDefined('searxng_base_url', parsedSettings.searxngBaseUrl);
          assignIfDefined('llm_provider', parsedSettings.llmProvider);
          assignIfDefined('llm_api_base_url', parsedSettings.llmApiBaseUrl);
          assignIfDefined('llm_api_key', parsedSettings.llmApiKey);
          assignIfDefined('llm_model_name', parsedSettings.llmModelName);

        } catch (e) {
          console.error("Error parsing appSettings from localStorage", e);
        }
      }
      
      thread.submit(payload); // Removed second argument { configurable: {} }
    },
    [thread]
  );

  const handleCancel = useCallback(() => {
    thread.stop();
    window.location.reload();
  }, [thread]);

  return (
    <div className="flex h-screen bg-neutral-800 text-neutral-100 font-sans antialiased">
      <main className="flex-1 flex flex-col overflow-hidden max-w-4xl mx-auto w-full">
        <header className="p-4 flex justify-between items-center border-b border-neutral-700">
          <h1 className="text-xl font-semibold">Pro Search Agent</h1>
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setIsSettingsDialogOpen(true)}
            aria-label="Open Settings"
          >
            <Cog className="h-5 w-5" />
          </Button>
        </header>

        <div
          className={`flex-1 overflow-y-auto ${
            thread.messages.length === 0 ? "flex" : ""
          }`}
        >
          {thread.messages.length === 0 ? (
            <WelcomeScreen
              handleSubmit={handleSubmit}
              isLoading={thread.isLoading}
              onCancel={handleCancel}
            />
          ) : (
            <ChatMessagesView
              messages={thread.messages}
              isLoading={thread.isLoading}
              scrollAreaRef={scrollAreaRef}
              onSubmit={handleSubmit}
              onCancel={handleCancel}
              liveActivityEvents={processedEventsTimeline}
              historicalActivities={historicalActivities}
            />
          )}
        </div>
      </main>
      <SettingsDialog
        isOpen={isSettingsDialogOpen}
        onClose={() => setIsSettingsDialogOpen(false)}
      />
    </div>
  );
}
