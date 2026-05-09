import Link from "next/link";
import { redirect } from "next/navigation";
import { Button, Header } from "@thomasbrunner-spec/design-system";
import { apiCall } from "@/lib/api";
import { createClient } from "@/lib/supabase/server";
import { LogoutButton } from "@/components/LogoutButton";
import { OfferList } from "@/components/OfferList";
import type { OfferListItem } from "@/lib/types/offer";

export default async function AngeboteListePage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  let offers: OfferListItem[] = [];
  let error: string | null = null;
  try {
    offers = await apiCall<OfferListItem[]>("/api/v1/offers");
  } catch (err) {
    error = err instanceof Error ? err.message : "Unknown error";
  }

  return (
    <>
      <Header
        appName="Angebote"
        rightSlot={
          <>
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

      <main className="container mx-auto max-w-5xl space-y-8 px-6 py-12">
        <div className="flex items-start justify-between gap-4">
          <div className="space-y-2">
            <h1 className="font-display text-3xl font-semibold tracking-tight">
              Angebote
            </h1>
            <p className="text-text-dim">
              Übersicht aller generierten und seeded Angebote, sortiert nach Datum.
            </p>
          </div>
          <Link href="/angebote/neu">
            <Button variant="primary">Neues Angebot</Button>
          </Link>
        </div>

        {error ? (
          <div className="rounded-md border border-danger/40 bg-danger/10 p-4 text-sm text-danger">
            Liste konnte nicht geladen werden: {error}
          </div>
        ) : (
          <OfferList offers={offers} />
        )}
      </main>
    </>
  );
}
