"use client";

import { useState } from "react";
import {
  Button,
  Card,
  Input,
  Label,
} from "@thomasbrunner-spec/design-system";

interface HaikuResponse {
  haiku: string;
  topic: string;
}

export function HelloHaikuDemo() {
  const [topic, setTopic] = useState("the Stratpool platform");
  const [haiku, setHaiku] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setHaiku(null);

    try {
      const response = await fetch("/api/hello/haiku", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic }),
      });

      if (!response.ok) {
        throw new Error(`Request failed: ${response.status}`);
      }

      const data: HaikuResponse = await response.json();
      setHaiku(data.haiku);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Card>
      <Card.Header>
        <Card.Title>Anthropic API smoke test</Card.Title>
        <Card.Description>
          This calls the FastAPI backend, which calls Claude. If you see a haiku, the full
          stack is working.
        </Card.Description>
      </Card.Header>
      <form onSubmit={handleSubmit}>
        <Card.Content className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="topic">Topic</Label>
            <Input
              id="topic"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              disabled={loading}
            />
          </div>
          {haiku && (
            <pre className="font-mono text-sm text-signal whitespace-pre-wrap p-4 bg-ink/40 rounded-md border border-slate/30">
              {haiku}
            </pre>
          )}
          {error && (
            <p className="text-sm text-danger" role="alert">
              {error}
            </p>
          )}
        </Card.Content>
        <Card.Footer>
          <Button type="submit" variant="primary" disabled={loading}>
            {loading ? "Generating…" : "Generate haiku"}
          </Button>
        </Card.Footer>
      </form>
    </Card>
  );
}
