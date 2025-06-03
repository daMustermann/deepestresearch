import React, { useState, useEffect, useCallback } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';

interface IAppSettings {
  searchApiProvider: string;
  searchApiKey: string;
  searxngBaseUrl: string;
  llmProvider: string;
  llmApiBaseUrl: string;
  llmApiKey: string;
  llmModelName: string;
}

interface SettingsDialogProps {
  isOpen: boolean;
  onClose: () => void;
}

const SettingsDialog: React.FC<SettingsDialogProps> = ({ isOpen, onClose }) => {
  const [searchApiProvider, setSearchApiProvider] = useState<string>('google');
  const [searchApiKey, setSearchApiKey] = useState<string>('');
  const [searxngBaseUrl, setSearxngBaseUrl] = useState<string>('');
  const [llmProvider, setLlmProvider] = useState<string>('google');
  const [llmApiBaseUrl, setLlmApiBaseUrl] = useState<string>('');
  const [llmApiKey, setLlmApiKey] = useState<string>('');
  const [llmModelName, setLlmModelName] = useState<string>('');

  const loadSettings = useCallback(() => {
    const storedSettings = localStorage.getItem('appSettings');
    if (storedSettings) {
      const settings: IAppSettings = JSON.parse(storedSettings);
      setSearchApiProvider(settings.searchApiProvider || 'google');
      setSearchApiKey(settings.searchApiKey || '');
      setSearxngBaseUrl(settings.searxngBaseUrl || '');
      setLlmProvider(settings.llmProvider || 'google');
      setLlmApiBaseUrl(settings.llmApiBaseUrl || '');
      setLlmApiKey(settings.llmApiKey || '');
      setLlmModelName(settings.llmModelName || '');
    }
  }, []);

  useEffect(() => {
    loadSettings();
  }, [loadSettings]);

  const saveSettings = () => {
    const settings: IAppSettings = {
      searchApiProvider,
      searchApiKey,
      searxngBaseUrl,
      llmProvider,
      llmApiBaseUrl,
      llmApiKey,
      llmModelName,
    };
    localStorage.setItem('appSettings', JSON.stringify(settings));
    onClose(); // Close dialog after saving
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <Card className="w-full max-w-lg">
        <CardHeader>
          <CardTitle>Application Settings</CardTitle>
          <CardDescription>Configure search and language model providers.</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* Search Settings */}
          <div className="space-y-2">
            <Label htmlFor="search-provider">Search API Provider</Label>
            <Select value={searchApiProvider} onValueChange={setSearchApiProvider}>
              <SelectTrigger id="search-provider">
                <SelectValue placeholder="Select search provider" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="google">Google</SelectItem>
                <SelectItem value="brave">Brave Search</SelectItem>
                <SelectItem value="searxng">SearXNG</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {searchApiProvider === 'brave' && (
            <div className="space-y-2">
              <Label htmlFor="brave-api-key">Brave API Key</Label>
              <Input
                id="brave-api-key"
                type="password"
                value={searchApiKey}
                onChange={(e) => setSearchApiKey(e.target.value)}
                placeholder="Enter Brave Search API Key"
              />
            </div>
          )}

          {searchApiProvider === 'searxng' && (
            <div className="space-y-2">
              <Label htmlFor="searxng-base-url">SearXNG Base URL</Label>
              <Input
                id="searxng-base-url"
                value={searxngBaseUrl}
                onChange={(e) => setSearxngBaseUrl(e.target.value)}
                placeholder="e.g., http://localhost:8888"
              />
            </div>
          )}

          {/* LLM Settings */}
          <div className="space-y-2">
            <Label htmlFor="llm-provider">LLM Provider</Label>
            <Select value={llmProvider} onValueChange={setLlmProvider}>
              <SelectTrigger id="llm-provider">
                <SelectValue placeholder="Select LLM provider" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="google">Google</SelectItem>
                <SelectItem value="custom">Custom (OpenAI-compatible)</SelectItem>
                {/* <SelectItem value="openai">OpenAI (Not implemented in backend yet)</SelectItem> */}
              </SelectContent>
            </Select>
          </div>

          {llmProvider === 'custom' && (
            <>
              <div className="space-y-2">
                <Label htmlFor="llm-api-base-url">LLM API Base URL</Label>
                <Input
                  id="llm-api-base-url"
                  value={llmApiBaseUrl}
                  onChange={(e) => setLlmApiBaseUrl(e.target.value)}
                  placeholder="Enter custom LLM API Base URL"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="llm-api-key">LLM API Key (Optional)</Label>
                <Input
                  id="llm-api-key"
                  type="password"
                  value={llmApiKey}
                  onChange={(e) => setLlmApiKey(e.target.value)}
                  placeholder="Enter custom LLM API Key"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="llm-model-name">LLM Model Name (Optional)</Label>
                <Input
                  id="llm-model-name"
                  value={llmModelName}
                  onChange={(e) => setLlmModelName(e.target.value)}
                  placeholder="e.g., gpt-3.5-turbo"
                />
              </div>
            </>
          )}
        </CardContent>
        <CardFooter className="flex justify-end space-x-2">
          <Button variant="outline" onClick={onClose}>
            Cancel
          </Button>
          <Button onClick={saveSettings}>Save Settings</Button>
        </CardFooter>
      </Card>
    </div>
  );
};

export default SettingsDialog;
