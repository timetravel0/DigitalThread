"use client";

import type { ComponentPropsWithoutRef, ReactNode } from "react";
import { Button, Textarea } from "@/components/ui";

type JsonTextareaFieldProps = ComponentPropsWithoutRef<typeof Textarea> & {
  label: string;
  description: string;
  example?: string;
  error?: string | null;
};

export function JsonTextareaField({ label, description, example, error, className, ...props }: JsonTextareaFieldProps) {
  return (
    <div className="space-y-2">
      <div className="space-y-1">
        <div className="text-sm font-medium text-text">{label}</div>
        <div className="text-xs text-muted">{description}</div>
      </div>
      <Textarea className={className} {...props} />
      {example ? (
        <div className="rounded-xl border border-dashed border-line bg-panel2 p-3 text-xs text-muted">
          <div className="mb-1 uppercase tracking-[0.2em]">Example</div>
          <pre className="whitespace-pre-wrap">{example}</pre>
        </div>
      ) : null}
      {error ? <div className="text-sm text-danger">{error}</div> : null}
    </div>
  );
}

type FormFooterProps = {
  submitLabel: string;
  cancelLabel?: string;
  busyLabel?: string;
  busy?: boolean;
  onCancel?: () => void;
  cancelDisabled?: boolean;
};

export function FormFooter({ submitLabel, cancelLabel = "Cancel", busyLabel, busy, onCancel, cancelDisabled }: FormFooterProps) {
  return (
    <div className="flex flex-wrap gap-2">
      {onCancel ? (
        <Button type="button" variant="secondary" onClick={onCancel} disabled={cancelDisabled}>
          {cancelLabel}
        </Button>
      ) : null}
      <Button type="submit" disabled={busy}>
        {busy && busyLabel ? busyLabel : submitLabel}
      </Button>
    </div>
  );
}

export function InlineHelp({ children }: { children: ReactNode }) {
  return <div className="text-xs text-muted">{children}</div>;
}
