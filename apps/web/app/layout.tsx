import "./globals.css";
import { ReactNode } from "react";
import { SidebarNav, TopBar } from "@/components/navigation";
import { Shell } from "@/components/ui";

export const metadata = {
  title: "ThreadLite",
  description: "Lightweight Digital Thread web application for engineering projects.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Shell sidebar={<SidebarNav />} header={<TopBar />}>
          {children}
        </Shell>
      </body>
    </html>
  );
}

