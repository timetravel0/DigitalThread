"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { cn } from "@/lib/utils";

export type ToastAction = {
  label: string;
  href: string;
};

export type ToastProps = {
  message: string;
  action?: ToastAction;
  onDismiss: () => void;
  duration?: number;
};

export function Toast({ message, action, onDismiss, duration = 5000 }: ToastProps) {
  const [mounted, setMounted] = useState(false);
  const [leaving, setLeaving] = useState(false);

  useEffect(() => {
    setMounted(true);
    const timer = window.setTimeout(() => {
      setLeaving(true);
    }, duration);
    return () => window.clearTimeout(timer);
  }, [duration]);

  useEffect(() => {
    if (!leaving) {
      return undefined;
    }
    const timer = window.setTimeout(() => {
      onDismiss();
    }, 200);
    return () => window.clearTimeout(timer);
  }, [leaving, onDismiss]);

  const dismiss = () => {
    if (!leaving) {
      setLeaving(true);
    }
  };

  return (
    <div
      role="status"
      aria-live="polite"
      className={cn(
        "fixed bottom-4 right-4 z-50 min-w-[280px] max-w-sm rounded-xl border border-line bg-panel px-4 py-3 shadow-glow transition-all duration-200 ease-out",
        mounted && !leaving ? "translate-y-0 opacity-100" : "translate-y-4 opacity-0",
        leaving ? "translate-y-2 opacity-0" : ""
      )}
    >
      <div className="flex items-start gap-4">
        <div className="min-w-0 flex-1">
          <div className="text-sm font-medium text-text">{message}</div>
          {action ? (
            <Link href={action.href} className="mt-2 inline-flex text-sm font-medium text-accent hover:underline">
              {action.label}
            </Link>
          ) : null}
        </div>
        <button
          type="button"
          className="rounded-md px-2 py-1 text-sm text-muted transition hover:bg-white/5 hover:text-text"
          onClick={dismiss}
          aria-label="Dismiss notification"
        >
          ×
        </button>
      </div>
    </div>
  );
}
