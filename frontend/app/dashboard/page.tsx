import Link from "next/link";
import { redirect } from "next/navigation";
import {
  Button,
  Card,
  Header,
  Badge,
} from "@thomasbrunner-spec/design-system";
import { createClient } from "@/lib/supabase/server";
import { LogoutButton } from "@/components/LogoutButton";
import { HelloHaikuDemo } from "@/components/HelloHaikuDemo";

export default async function DashboardPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  return (
    <>
      <Header
        appName="App"
        rightSlot={
          <>
            <span className="font-mono text-xs text-text-dim hidden sm:inline">
              {user.email}
            </span>
            <LogoutButton />
          </>
        }
      />

      <main className="container max-w-4xl mx-auto px-6 py-12 space-y-8">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-2">
            <h1 className="font-display text-3xl font-semibold tracking-tight">
              Dashboard
            </h1>
            <p className="text-text-dim">
              You're signed in as <code className="font-mono text-signal">{user.email}</code>
            </p>
          </div>
          <div className="flex gap-2">
            <Link href="/angebote">
              <Button variant="secondary">Angebote</Button>
            </Link>
            <Link href="/angebote/neu">
              <Button variant="primary">Neues Angebot</Button>
            </Link>
          </div>
        </div>

        <Card>
          <Card.Header>
            <div className="flex items-center justify-between">
              <Card.Title>Platform check</Card.Title>
              <Badge variant="success">CONNECTED</Badge>
            </div>
            <Card.Description>
              Your app is connected to Supabase auth and the StratPool design system.
            </Card.Description>
          </Card.Header>
          <Card.Content className="grid grid-cols-2 gap-4 text-sm">
            <div className="flex flex-col gap-1">
              <span className="text-text-muted">User ID</span>
              <code className="font-mono text-xs text-text-dim truncate">{user.id}</code>
            </div>
            <div className="flex flex-col gap-1">
              <span className="text-text-muted">Last sign-in</span>
              <code className="font-mono text-xs text-text-dim">
                {user.last_sign_in_at?.slice(0, 19).replace("T", " ") ?? "—"}
              </code>
            </div>
          </Card.Content>
        </Card>

        <HelloHaikuDemo />
      </main>
    </>
  );
}
