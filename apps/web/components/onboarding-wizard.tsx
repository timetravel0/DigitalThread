"use client";

import { useEffect, useMemo, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui";
import type { DomainProfile, LabelSet } from "@/lib/labels";
import { cn } from "@/lib/utils";

type WizardStep = 1 | 2 | 3;

export function OnboardingWizard({
  projectId,
  profile,
  labels,
  children,
}: {
  projectId: string;
  profile: DomainProfile;
  labels: LabelSet;
  children: ReactNode;
}) {
  const router = useRouter();
  const [visible, setVisible] = useState(false);
  const [leaving, setLeaving] = useState(false);
  const [step, setStep] = useState<WizardStep>(1);
  const storageKey = useMemo(() => `threadlite-onboarding-done-${projectId}`, [projectId]);

  useEffect(() => {
    try {
      const done = window.localStorage.getItem(storageKey);
      if (!done) setVisible(true);
    } catch {
      // ignore storage failures
    }
  }, [storageKey]);

  useEffect(() => {
    if (!visible) return undefined;

    const focusFirst = () => {
      const focusable = document.querySelector<HTMLElement>(
        '[data-onboarding-wizard] button:not([disabled]), [data-onboarding-wizard] a[href], [data-onboarding-wizard] [tabindex]:not([tabindex="-1"])'
      );
      focusable?.focus();
    };
    const timer = window.setTimeout(focusFirst, 0);

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        event.preventDefault();
        dismiss(true);
        return;
      }
      if (event.key !== "Tab") return;
      const focusable = Array.from(
        document.querySelectorAll<HTMLElement>(
          '[data-onboarding-wizard] button:not([disabled]), [data-onboarding-wizard] a[href], [data-onboarding-wizard] [tabindex]:not([tabindex="-1"])'
        )
      );
      if (!focusable.length) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      const active = document.activeElement as HTMLElement | null;
      if (event.shiftKey) {
        if (!active || active === first) {
          event.preventDefault();
          last.focus();
        }
      } else if (!active || active === last) {
        event.preventDefault();
        first.focus();
      }
    };

    window.addEventListener("keydown", onKeyDown);
    return () => {
      window.clearTimeout(timer);
      window.removeEventListener("keydown", onKeyDown);
    };
  }, [visible]);

  const persistDone = () => {
    try {
      window.localStorage.setItem(storageKey, "1");
    } catch {
      // ignore storage failures
    }
  };

  const dismiss = (skipPersist = false) => {
    if (!skipPersist) {
      persistDone();
    }
    setLeaving(true);
    window.setTimeout(() => {
      setVisible(false);
      setLeaving(false);
      setStep(1);
    }, 200);
  };

  const finish = () => {
    persistDone();
    dismiss(true);
    router.push(`/projects/${projectId}/requirements`);
  };

  const wizardVisibleClass = visible && !leaving ? "translate-y-0 opacity-100" : "translate-y-3 opacity-0";

  return (
    <>
      {children}
      {visible ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 px-4">
          <div
            data-onboarding-wizard
            role="dialog"
            aria-modal="true"
            aria-labelledby="onboarding-title"
            aria-describedby="onboarding-description"
            className={cn(
              "max-w-lg w-full rounded-2xl border border-line bg-panel p-8 shadow-glow transition-all duration-200 ease-out",
              wizardVisibleClass
            )}
          >
            <div className="mb-6 flex items-center justify-between gap-4">
              <div className="flex gap-2">
                {[1, 2, 3].map((item) => (
                  <span
                    key={item}
                    className={`h-2.5 w-2.5 rounded-full transition-colors ${step >= item ? "bg-accent" : "bg-white/20"}`}
                  />
                ))}
              </div>
              <button type="button" onClick={() => dismiss(true)} className="text-sm text-muted hover:text-text">
                Skip
              </button>
            </div>

            {step === 1 ? (
              <div className="space-y-5">
                <div>
                  <h2 id="onboarding-title" className="text-2xl font-semibold text-text">
                    Welcome to your Digital Thread
                  </h2>
                  <p id="onboarding-description" className="mt-2 text-sm text-muted">
                    A digital thread connects requirements, blocks, tests, traceability, and evidence so you can follow the story of your project end to end.
                  </p>
                </div>
                <div className="grid gap-3 text-sm text-text sm:grid-cols-5">
                  {["Requirements", "Blocks", "Tests", "Traceability", "Evidence"].map((item, index) => (
                    <div key={item} className="flex items-center gap-3 rounded-xl border border-line bg-panel2 px-3 py-2">
                      <span className="flex h-6 w-6 items-center justify-center rounded-full bg-accent/15 text-xs font-semibold text-accent">{index + 1}</span>
                      <span>{item}</span>
                      {index < 4 ? <span className="text-muted">→</span> : null}
                    </div>
                  ))}
                </div>
                <div className="flex justify-end">
                  <Button onClick={() => setStep(2)}>Next →</Button>
                </div>
              </div>
            ) : step === 2 ? (
              <div className="space-y-5">
                <div>
                  <h2 id="onboarding-title" className="text-2xl font-semibold text-text">
                    The recommended flow
                  </h2>
                  <p id="onboarding-description" className="mt-2 text-sm text-muted">
                    Start with one clear requirement, then connect the rest of the thread around it.
                  </p>
                </div>
                <ol className="space-y-2 text-sm text-text">
                  <li>1. Create your first {labels.requirements}</li>
                  <li>2. Add {labels.blocks} that implement them</li>
                  <li>3. Define {labels.testCases} for each {labels.requirements}</li>
                  <li>4. Connect them in the Traceability view</li>
                </ol>
                <div className="flex items-center justify-between gap-3">
                  <button type="button" className="text-sm text-muted hover:text-text" onClick={() => setStep(1)}>
                    Back
                  </button>
                  <Button onClick={() => setStep(3)}>Next →</Button>
                </div>
              </div>
            ) : (
              <div className="space-y-5">
                <div>
                  <h2 id="onboarding-title" className="text-2xl font-semibold text-text">
                    Start with your first {labels.requirements}
                  </h2>
                  <p id="onboarding-description" className="mt-2 text-sm text-muted">
                    You can begin with a single clear item and grow the thread as your project evolves.
                  </p>
                </div>
                <div className="flex items-center justify-between gap-3">
                  <button type="button" className="text-sm text-muted hover:text-text" onClick={() => setStep(2)}>
                    Back
                  </button>
                  <div className="flex items-center gap-3">
                    <button type="button" className="text-sm text-muted hover:text-text" onClick={() => dismiss(true)}>
                      Skip, I&apos;ll explore on my own
                    </button>
                    <Button onClick={finish}>{`Create my first ${labels.requirements}`}</Button>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      ) : null}
    </>
  );
}
