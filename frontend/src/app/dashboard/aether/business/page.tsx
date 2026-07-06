"use client";

import { Brain, Globe, Play, RefreshCw } from "lucide-react";
import { useState } from "react";
import { BusinessProfileView } from "@/components/aether/business-profile";
import { KnowledgeBase } from "@/components/aether/knowledge";
import {
  AetherEmpty, ErrorNote, FadeIn, GlassCard, LoadingAgents, Textarea,
} from "@/components/aether/shared";
import { Loading } from "@/components/dashboard/common";
import { PageHeader } from "@/components/dashboard/shell";
import { Button, Input, Label } from "@/components/ui";
import { useAnalyzeBusiness, useBusinessProfile } from "@/lib/aether";

export default function BusinessIntelPage() {
  const profile = useBusinessProfile();
  const analyze = useAnalyzeBusiness();

  const [website, setWebsite] = useState("");
  const [notes, setNotes] = useState("");
  const [socials, setSocials] = useState("");
  const [showForm, setShowForm] = useState(false);

  const run = () => {
    analyze.mutate(
      {
        website_url: website.trim() || undefined,
        extra_text: notes.trim() || undefined,
        social_urls: socials.split(/[\n,]+/).map((s) => s.trim()).filter(Boolean),
      },
      { onSuccess: () => setShowForm(false) },
    );
  };

  const hasProfile = !!profile.data;
  const formVisible = showForm || (!hasProfile && !profile.isLoading);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Business Intelligence"
        subtitle="Aether deep-scans your brand — offers, voice, funnel, customers — to power every other module."
        action={
          hasProfile ? (
            <Button variant="outline" size="sm" onClick={() => setShowForm((v) => !v)}>
              <RefreshCw className="h-3.5 w-3.5" /> Re-analyze
            </Button>
          ) : undefined
        }
      />

      {profile.isLoading && <Loading />}
      <ErrorNote error={profile.error ?? undefined} />

      {formVisible && !analyze.isPending && (
        <FadeIn>
          <GlassCard glow className="p-5 sm:p-6">
            <div className="grid gap-4 lg:grid-cols-2">
              <div className="space-y-4">
                <div className="space-y-1.5">
                  <Label>Website URL</Label>
                  <div className="relative">
                    <Globe className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                    <Input value={website} onChange={(e) => setWebsite(e.target.value)} placeholder="https://yourbrand.com" className="pl-9" />
                  </div>
                </div>
                <div className="space-y-1.5">
                  <Label>Social profiles <span className="text-xs font-normal text-muted-foreground">(one per line)</span></Label>
                  <Textarea
                    value={socials}
                    onChange={(e) => setSocials(e.target.value)}
                    placeholder={"https://instagram.com/yourbrand\nhttps://tiktok.com/@yourbrand"}
                    className="min-h-[72px]"
                  />
                </div>
              </div>
              <div className="space-y-1.5">
                <Label>Extra context <span className="text-xs font-normal text-muted-foreground">(optional notes for the agents)</span></Label>
                <Textarea
                  value={notes}
                  onChange={(e) => setNotes(e.target.value)}
                  placeholder="Anything the AI should know — bestsellers, margins, current ad accounts, brand no-gos…"
                  className="min-h-[152px]"
                />
              </div>
            </div>
            <div className="mt-4 flex items-center gap-3">
              <Button
                onClick={run}
                disabled={analyze.isPending || (!website.trim() && !notes.trim() && !socials.trim())}
                className="bg-gradient-to-r from-violet-600 to-indigo-600 hover:opacity-90"
              >
                <Play className="h-4 w-4" /> Run deep analysis
              </Button>
              {hasProfile && <Button variant="ghost" size="sm" onClick={() => setShowForm(false)}>Cancel</Button>}
            </div>
            <div className="mt-3"><ErrorNote error={analyze.error ?? undefined} /></div>
          </GlassCard>
        </FadeIn>
      )}

      {analyze.isPending && (
        <LoadingAgents label="Analyzing your business" sub="Scraping, reading and reasoning across your site and socials — 30–90 seconds." />
      )}

      {!profile.isLoading && !hasProfile && !formVisible && !analyze.isPending && (
        <AetherEmpty
          icon={Brain}
          title="No business profile yet"
          desc="Point Aether at your website and socials and it will map your offers, positioning, funnel leaks and ideal customers."
          cta={<Button onClick={() => setShowForm(true)}><Play className="h-4 w-4" /> Analyze my business</Button>}
        />
      )}

      {hasProfile && !analyze.isPending && <BusinessProfileView profile={profile.data!} />}

      <KnowledgeBase />
    </div>
  );
}
