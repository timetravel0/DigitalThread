"use client";

import Link from "next/link";
import { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function Button({
  children,
  className,
  href,
  variant = "primary",
  type = "button",
  onClick,
}: {
  children: ReactNode;
  className?: string;
  href?: string;
  variant?: "primary" | "secondary" | "ghost" | "danger";
  type?: "button" | "submit";
  onClick?: () => void;
}) {
  const classes = cn(
    "inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition",
    variant === "primary" && "bg-accent text-slate-950 hover:opacity-90",
    variant === "secondary" && "bg-panel2 text-text border border-line hover:border-accent/60",
    variant === "ghost" && "text-text hover:bg-white/5",
    variant === "danger" && "bg-danger text-white hover:opacity-90",
    className
  );
  const content = children;
  if (href) {
    return (
      <Link href={href} className={classes}>
        {content}
      </Link>
    );
  }
  return (
    <button type={type} className={classes} onClick={onClick}>
      {content}
    </button>
  );
}

export function Card({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("rounded-2xl border border-line bg-panel shadow-glow", className)}>{children}</div>;
}

export function CardHeader({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("border-b border-line px-5 py-4", className)}>{children}</div>;
}

export function CardBody({ children, className }: { children: ReactNode; className?: string }) {
  return <div className={cn("px-5 py-4", className)}>{children}</div>;
}

export function Badge({ children, tone = "neutral" }: { children: ReactNode; tone?: "neutral" | "success" | "warning" | "danger" | "accent" }) {
  const tones = {
    neutral: "bg-white/5 text-text border-white/10",
    success: "bg-success/15 text-success border-success/30",
    warning: "bg-yellow-400/15 text-yellow-200 border-yellow-400/30",
    danger: "bg-danger/15 text-danger border-danger/30",
    accent: "bg-accent/15 text-accent border-accent/30",
  };
  return <span className={cn("inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium", tones[tone])}>{children}</span>;
}

export function Input(props: React.InputHTMLAttributes<HTMLInputElement>) {
  return <input {...props} className={cn("w-full rounded-xl border border-line bg-slate-950/40 px-3 py-2 text-sm text-text outline-none placeholder:text-slate-500 focus:border-accent", props.className)} />;
}

export function Textarea(props: React.TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea {...props} className={cn("w-full rounded-xl border border-line bg-slate-950/40 px-3 py-2 text-sm text-text outline-none placeholder:text-slate-500 focus:border-accent", props.className)} />;
}

export function Select(props: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return <select {...props} className={cn("w-full rounded-xl border border-line bg-slate-950/40 px-3 py-2 text-sm text-text outline-none focus:border-accent", props.className)} />;
}

export function StatCard({ label, value, sub }: { label: string; value: string | number; sub?: string }) {
  return (
    <Card>
      <CardBody>
        <div className="text-xs uppercase tracking-[0.2em] text-muted">{label}</div>
        <div className="mt-2 text-3xl font-semibold text-text">{value}</div>
        {sub ? <div className="mt-1 text-sm text-muted">{sub}</div> : null}
      </CardBody>
    </Card>
  );
}

export function EmptyState({ title, description, action }: { title: string; description: string; action?: ReactNode }) {
  return (
    <Card className="border-dashed">
      <CardBody>
        <div className="text-lg font-semibold text-text">{title}</div>
        <div className="mt-2 text-sm text-muted">{description}</div>
        {action ? <div className="mt-4">{action}</div> : null}
      </CardBody>
    </Card>
  );
}

export function SectionTitle({ title, description, action }: { title: string; description?: string; action?: ReactNode }) {
  return (
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div>
        <h2 className="text-xl font-semibold text-text">{title}</h2>
        {description ? <p className="mt-1 text-sm text-muted">{description}</p> : null}
      </div>
      {action}
    </div>
  );
}

export function Shell({ sidebar, header, children }: { sidebar: ReactNode; header: ReactNode; children: ReactNode }) {
  return (
    <div className="min-h-screen bg-[radial-gradient(circle_at_top_left,_rgba(124,219,255,0.10),_transparent_28%),linear-gradient(180deg,_#07101f,_#0b1020_40%,_#090d18)] text-text">
      <div className="mx-auto flex min-h-screen max-w-[1600px]">
        <aside className="hidden w-72 shrink-0 border-r border-white/10 bg-black/10 p-5 lg:block">{sidebar}</aside>
        <div className="flex min-w-0 flex-1 flex-col">
          <header className="border-b border-white/10 bg-black/10 px-4 py-4 backdrop-blur">{header}</header>
          <main className="flex-1 px-4 py-6 lg:px-6">{children}</main>
        </div>
      </div>
    </div>
  );
}

