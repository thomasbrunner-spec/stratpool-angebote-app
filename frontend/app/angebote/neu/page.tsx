import Link from "next/link";
import { redirect } from "next/navigation";
import { Button, Header } from "@thomasbrunner-spec/design-system";
import { createClient } from "@/lib/supabase/server";
import { LogoutButton } from "@/components/LogoutButton";
import { GenerateForm } from "./GenerateForm";

export default async function NeuesAngebotPage() {
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
        appName="Angebote"
        rightSlot={
          <>
            <Link href="/angebote" className="text-xs text-text-dim hover:text-text">
              Angebote
            </Link>
            <Link href="/dashboard" className="text-xs text-text-dim hover:text-text">
              Dashboard
            </Link>
            <span className="font-mono text-xs text-text-dim hidden sm:inline">
              {user.email}
            </span>
            <LogoutButton />
          </>
        }
      />

      <main className="container mx-auto max-w-4xl space-y-8 px-6 py-12">
        <div className="space-y-2">
          <h1 className="font-display text-3xl font-semibold tracking-tight">
            Neues Angebot
          </h1>
          <p className="text-text-dim">
            Discovery-Daten eingeben, Pipeline läuft, Vorschau erscheint hier.
          </p>
        </div>

        <GenerateForm />
      </main>
    </>
  );
}
