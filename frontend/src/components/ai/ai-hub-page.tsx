"use client";

import Link from "next/link";
import {
  Clock,
  Cpu,
  FileText,
  Settings,
  Sparkles,
  type LucideIcon,
} from "lucide-react";

import { PageContainer, PageHeader } from "@/components/layout/page-header";

type HubLink = {
  href: string;
  title: string;
  description: string;
  icon: LucideIcon;
};

const LINKS: HubLink[] = [
  {
    href: "/ai/settings",
    title: "Settings",
    description: "Providers, models, credentials, and studio defaults.",
    icon: Settings,
  },
  {
    href: "/ai/prompts",
    title: "Prompt Library",
    description: "Manage reusable prompts and version history.",
    icon: FileText,
  },
  {
    href: "/ai/jobs",
    title: "Job Monitor",
    description: "Track queued and running generation jobs.",
    icon: Clock,
  },
  {
    href: "/ai/generations",
    title: "Generation History",
    description: "Browse completed outputs, tokens, and cost.",
    icon: Cpu,
  },
];

export function AiHubPage() {
  return (
    <PageContainer>
      <PageHeader
        title="AI Foundation"
        description="Configure providers, prompts, and monitor generation infrastructure."
        actions={
          <Sparkles className="h-8 w-8 text-brand-orange" aria-hidden />
        }
      />

      <div className="grid gap-4 sm:grid-cols-2">
        {LINKS.map((item) => {
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className="panel group flex flex-col gap-3 p-5 transition hover:border-brand-orange/40 hover:bg-surface-hover"
            >
              <div className="flex items-center gap-3">
                <span className="inline-flex h-10 w-10 items-center justify-center rounded-lg bg-brand-orange/10 text-brand-orange">
                  <Icon className="h-5 w-5" aria-hidden />
                </span>
                <h2 className="text-base font-semibold text-foreground group-hover:text-brand-orange">
                  {item.title}
                </h2>
              </div>
              <p className="text-sm text-muted-foreground">{item.description}</p>
            </Link>
          );
        })}
      </div>
    </PageContainer>
  );
}
