"use client";

import { createContext, useCallback, useContext, useRef, useState, ReactNode } from "react";
import { Toast, type ToastAction } from "@/components/toast";

export type ToastOptions = {
  message: string;
  action?: ToastAction;
  duration?: number;
};

type ToastState = ToastOptions & {
  id: number;
};

type ToastContextValue = {
  showToast: (options: ToastOptions) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toast, setToast] = useState<ToastState | null>(null);
  const sequence = useRef(0);

  const showToast = useCallback((options: ToastOptions) => {
    sequence.current += 1;
    setToast({
      id: sequence.current,
      message: options.message,
      action: options.action,
      duration: options.duration,
    });
  }, []);

  const activeToastId = toast?.id;
  const handleDismiss = useCallback(() => {
    setToast((current) => (current?.id === activeToastId ? null : current));
  }, [activeToastId]);

  return (
    <ToastContext.Provider value={{ showToast }}>
      {children}
      {toast ? (
        <Toast
          key={toast.id}
          message={toast.message}
          action={toast.action}
          duration={toast.duration}
          onDismiss={handleDismiss}
        />
      ) : null}
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}
