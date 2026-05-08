"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Button,
  Card,
  Input,
  Label,
  Logo,
} from "@thomasbrunner-spec/design-system";
import { createClient } from "@/lib/supabase/client";

export default function LoginPage() {
  const router = useRouter();
  const supabase = createClient();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const { error: authError } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (authError) {
      setError(authError.message);
      setLoading(false);
      return;
    }

    router.push("/dashboard");
    router.refresh();
  };

  return (
    <main className="min-h-screen flex items-center justify-center px-6">
      <div className="w-full max-w-md flex flex-col items-center gap-8">
        <Logo variant="primary-dark" height={40} />

        <Card className="w-full">
          <Card.Header>
            <Card.Title>Welcome back</Card.Title>
            <Card.Description>Sign in to your account</Card.Description>
          </Card.Header>

          <form onSubmit={handleSubmit}>
            <Card.Content className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  autoComplete="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  disabled={loading}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <Input
                  id="password"
                  type="password"
                  autoComplete="current-password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  disabled={loading}
                />
              </div>

              {error && (
                <p className="text-sm text-danger" role="alert">
                  {error}
                </p>
              )}
            </Card.Content>

            <Card.Footer>
              <Button
                type="submit"
                variant="primary"
                className="w-full"
                disabled={loading}
              >
                {loading ? "Signing in…" : "Sign in"}
              </Button>
            </Card.Footer>
          </form>
        </Card>
      </div>
    </main>
  );
}
