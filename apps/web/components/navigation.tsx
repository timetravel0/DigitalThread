"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const items = [
  { href: "/dashboard", label: "Dashboard" },
  { href: "/projects", label: "Projects" },
];

export function SidebarNav() {
  const pathname = usePathname();
  return (
    <div className="flex h-full flex-col gap-6">
      <div>
        <div className="text-xs uppercase tracking-[0.3em] text-accent">ThreadLite</div>
        <div className="mt-2 text-2xl font-semibold">Digital Thread MVP</div>
        <p className="mt-2 text-sm text-muted">Traceability, baselines, impact, and evidence for SME engineering teams.</p>
      </div>
      <nav className="space-y-1">
        {items.map((item) => {
          const active = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "block rounded-xl border px-3 py-2 text-sm transition",
                active ? "border-accent/50 bg-accent/10 text-accent" : "border-transparent text-text hover:bg-white/5"
              )}
            >
              {item.label}
            </Link>
          );
        })}
      </nav>
      <div className="mt-auto rounded-2xl border border-line bg-panel2 p-4 text-sm text-muted">
        Seed the demo project from the dashboard to populate the drone example.
      </div>
    </div>
  );
}

export function TopBar() {
  return (
    <div className="flex items-center justify-between gap-4">
      <div>
        <div className="text-xs uppercase tracking-[0.25em] text-muted">ThreadLite</div>
        <div className="text-lg font-semibold">Lightweight Digital Thread</div>
      </div>
      <div className="hidden text-sm text-muted md:block">FastAPI + Next.js + PostgreSQL</div>
    </div>
  );
}

