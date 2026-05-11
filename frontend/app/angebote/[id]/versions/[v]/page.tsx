import Link from "next/link";
import { notFound, redirect } from "next/navigation";
import { Card, Header } from "@thomasbrunner-spec/design-system";
import { apiCall } from "@/lib/api";
import { createClient } from "@/lib/supabase/server";
import { LogoutButton } from "@/components/LogoutButton";
import { OfferContentView } from "@/components/OfferContentView";
import type { OfferVersionDetail } from "@/lib/types/offer";

const DATE_FORMAT = new Intl.DateTimeFormat("de-DE", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

interface PageProps {
  params: Promise<{ id: string; v: string }>;
}

export default async function AngebotVersionPage({ params }: PageProps) {
  const { id, v } = await params;
  const versionNumber = Number.parseInt(v, 10);
  if (!Number.isFinite(versionNumber)) {
    notFound();
  }

  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  let version: OfferVersionDetail;
  try {
    version = await apiCall<OfferVersionDetail>(
      `/api/v1/offers/${id}/versions/${versionNumber}`,
    );
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    if (message.includes("404") || message.includes("410")) {
      notFound();
    }
    throw err;
  }

  return (
    <>
      <Header
        appName="Angebote"
        rightSlot={
          <>
            <Link href="/angebote" className="text-xs text-text-dim hover:text-text">
              Liste
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
          <Link
            href={`/angebote/${id}`}
            className="font-mono text-xs text-text-muted hover:text-signal"
          >
            ← zurück zum aktuellen Angebot
          </Link>
          <div className="space-y-1">
            <div className="flex items-baseline gap-3">
              <h1 className="font-display text-3xl font-semibold tracking-tight">
                {version.content.angebot_titel}
              </h1>
              <span className="font-mono text-sm text-signal">
                v{version.version_number}
              </span>
            </div>
            <p className="text-text-dim">
              Für <span className="text-text">{version.content.client_name}</span>
              <span className="text-text-muted">
                {" "}
                · erstellt {DATE_FORMAT.format(new Date(version.created_at))}
              </span>
            </p>
          </div>
        </div>

        <Card>
          <Card.Content className="space-y-3 py-4">
            <p className="font-mono text-xs uppercase tracking-wider text-text-muted">
              Schreibgeschützte Ansicht einer früheren Version
            </p>
            {version.revision_notes && (
              <div className="space-y-1">
                <div className="font-mono text-xs uppercase tracking-wider text-text-muted">
                  Revisions-Notiz
                </div>
                <p className="text-sm text-text leading-relaxed">
                  {version.revision_notes}
                </p>
              </div>
            )}
          </Card.Content>
        </Card>

        <OfferContentView content={version.content} />
      </main>
    </>
  );
}
