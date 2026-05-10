import Link from "next/link";
import { redirect } from "next/navigation";
import { Card, Header } from "@thomasbrunner-spec/design-system";
import { apiCall } from "@/lib/api";
import { createClient } from "@/lib/supabase/server";
import { LogoutButton } from "@/components/LogoutButton";
import { PromptBlock } from "@/components/PromptBlock";
import type { PromptsResponse } from "@/lib/types/prompts";

export default async function PromptsPage() {
  const supabase = await createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  const data = await apiCall<PromptsResponse>("/api/v1/prompts");

  return (
    <>
      <Header
        appName="Angebote"
        rightSlot={
          <>
            <Link href="/dashboard" className="text-xs text-text-dim hover:text-text">
              Dashboard
            </Link>
            <Link href="/angebote" className="text-xs text-text-dim hover:text-text">
              Angebote
            </Link>
            <span className="font-mono text-xs text-text-dim hidden sm:inline">
              {user.email}
            </span>
            <LogoutButton />
          </>
        }
      />

      <main className="container mx-auto max-w-5xl space-y-10 px-6 py-12">
        <div className="space-y-2">
          <h1 className="font-display text-3xl font-semibold tracking-tight">
            Prompts
          </h1>
          <p className="text-text-dim">
            Read-only-Einsicht: was Generate und Render an Claude schicken. Inputs
            sind als Platzhalter (&lt;KUNDE&gt; usw.) gerendert.
          </p>
        </div>

        <section className="space-y-6">
          <SectionHeader title="Generate" subtitle="Discovery → strukturiertes Angebots-JSON" />

          <Meta
            rows={[
              ["Modell", data.generate.model],
              ["max_tokens", String(data.generate.max_tokens)],
            ]}
          />

          <Card>
            <Card.Header>
              <Card.Title>System-Prompt</Card.Title>
              <Card.Description>
                Statisch. Kommt vor jedem Generate als erster System-Block.
              </Card.Description>
            </Card.Header>
            <Card.Content>
              <PromptBlock label="SYSTEM_INSTRUCTIONS" text={data.generate.system} />
            </Card.Content>
          </Card>

          <Card>
            <Card.Header>
              <Card.Title>Skelett-Referenz</Card.Title>
              <Card.Description>
                Wird an den System-Prompt angehängt — beschreibt die ERA-Struktur.
              </Card.Description>
            </Card.Header>
            <Card.Content>
              <PromptBlock label="prompts/offer_skeleton.md" text={data.generate.skeleton} />
            </Card.Content>
          </Card>

          <Card>
            <Card.Header>
              <Card.Title>User-Message (Beispiel)</Card.Title>
              <Card.Description>{data.generate.user_message_notes}</Card.Description>
            </Card.Header>
            <Card.Content>
              <PromptBlock
                label="aus _build_user_message"
                text={data.generate.user_message_example}
              />
            </Card.Content>
          </Card>
        </section>

        <section className="space-y-6">
          <SectionHeader
            title="Render"
            subtitle="Discovery + Berater → ERA-CI Word/PowerPoint via Skills + Code-Execution"
          />

          <Meta
            rows={[
              ["Modell", data.render.model],
              ["max_tokens", String(data.render.max_tokens)],
              ["Beta-Header", data.render.betas.join(", ")],
              ...Object.entries(data.render.skills).map(
                ([k, v]) => [`skill: ${k}`, v] as [string, string]
              ),
            ]}
          />

          <Card>
            <Card.Header>
              <Card.Title>User-Message für PowerPoint</Card.Title>
              <Card.Description>{data.render.user_message_notes}</Card.Description>
            </Card.Header>
            <Card.Content>
              <PromptBlock label="pptx" text={data.render.pptx_user_message_example} />
            </Card.Content>
          </Card>

          <Card>
            <Card.Header>
              <Card.Title>User-Message für Word</Card.Title>
              <Card.Description>
                Identische Struktur, andere Skill-Referenz und Output-Pfad.
              </Card.Description>
            </Card.Header>
            <Card.Content>
              <PromptBlock label="docx" text={data.render.word_user_message_example} />
            </Card.Content>
          </Card>
        </section>
      </main>
    </>
  );
}

function SectionHeader({ title, subtitle }: { title: string; subtitle: string }) {
  return (
    <div className="space-y-1 border-b border-slate/30 pb-3">
      <h2 className="font-display text-2xl font-semibold tracking-tight">{title}</h2>
      <p className="text-sm text-text-muted">{subtitle}</p>
    </div>
  );
}

function Meta({ rows }: { rows: [string, string][] }) {
  return (
    <div className="grid grid-cols-1 gap-3 font-mono text-xs sm:grid-cols-2">
      {rows.map(([k, v]) => (
        <div key={k} className="flex flex-col gap-1">
          <span className="text-text-muted">{k}</span>
          <span className="truncate text-text-dim">{v}</span>
        </div>
      ))}
    </div>
  );
}
