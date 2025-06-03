import { useStream } from "@langchain/langgraph-sdk/react";
import type { Message } from "@langchain/langgraph-sdk";
import { useState, useEffect, useRef, useCallback } from "react";
import { ProcessedEvent } from "@/components/ActivityTimeline";
import { WelcomeScreen } from "@/components/WelcomeScreen";
import { ChatMessagesView } from "@/components/ChatMessagesView";
import SettingsDialog from "@/components/SettingsDialog"; // Import SettingsDialog
import { Button } from "@/components/ui/button"; // Import Button
import { Cog } from "lucide-react"; // Import an icon for the button

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

  const thread = useStream<{
    messages: Message[];
    initial_search_query_count: number;
    max_research_loops: number;
    reasoning_model: string;
    // Add configurable to the type definition for useStream
    configurable?: Record<string, any>;
  }>({
    apiUrl: import.meta.env.DEV
      ? "http://localhost:2024"
      : "http://localhost:8123",
    assistantId: "agent",
    messagesKey: "messages",
    onFinish: (event: any) => {
      console.log(event);
    },
    onUpdateEvent: (event: any) => {
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
          ...new Set(sources.map((s: any) => s.label).filter(Boolean)),
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

      // convert effort to, initial_search_query_count and max_research_loops
      // low means max 1 loop and 1 query
      // medium means max 3 loops and 3 queries
      // high means max 10 loops and 5 queries
      let initial_search_query_count = 0;
      let max_research_loops = 0;
      switch (effort) {
        case "low":
          initial_search_query_count = 1;
          max_research_loops = 1;
          break;
        case "medium":
          initial_search_query_count = 3;
          max_research_loops = 3;
          break;
        case "high":
          initial_search_query_count = 5;
          max_research_loops = 10;
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

      // Retrieve and map settings for the backend
      const configurable: Record<string, any> = {};
      const settingsString = localStorage.getItem('appSettings');
      if (settingsString) {
        try {
          const parsedSettings = JSON.parse(settingsString);

          const assignIfDefined = (targetKey: string, value: any) => {
            // Ensure that we only pass the value if it's not empty, null, or undefined.
            // For boolean false, it should still be passed if that's a valid setting.
            // For this use case, empty strings are treated as "not set".
            if (value !== undefined && value !== null && value !== '') {
              configurable[targetKey] = value;
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
          // Proceed with empty configurable or default if error
        }
      }

      thread.submit({
        messages: newMessages,
        initial_search_query_count: initial_search_query_count,
        max_research_loops: max_research_loops,
        reasoning_model: model, // This will be overridden by llm_model_name if llm_provider is custom/openai
        configurable: configurable,
      });
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
        {/* Header with Settings Button */}
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
