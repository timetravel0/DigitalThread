import "./globals.css";
import { ReactNode } from "react";
import { SidebarNav, TopBar } from "@/components/navigation";
import { Shell } from "@/components/ui";
import { ToastProvider } from "@/lib/toast-context";

export const metadata = {
  title: "ThreadLite",
  description: "Lightweight Digital Thread web application for engineering projects.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <ToastProvider>
          <Shell sidebar={<SidebarNav />} header={<TopBar />}>
            {children}
          </Shell>
        </ToastProvider>
      </body>
    </html>
  );
}
