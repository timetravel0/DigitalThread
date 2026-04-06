import fs from "fs/promises";
import path from "path";

export type DocSlug = "readme" | "user-guide" | "use-cases" | "platform-logic" | "target-architecture" | "implementation-backlog" | "gap-analysis";

export interface DocEntry {
  slug: DocSlug;
  title: string;
  description: string;
  filePath: string;
}

export const DOCS: DocEntry[] = [
  {
    slug: "readme",
    title: "Product README",
    description: "Overview, setup, architecture, and product context.",
    filePath: path.resolve(process.cwd(), "..", "..", "README.md"),
  },
  {
    slug: "user-guide",
    title: "User Guide",
    description: "How to use each module and workflow in the application.",
    filePath: path.resolve(process.cwd(), "..", "..", "docs", "user-guide.md"),
  },
  {
    slug: "use-cases",
    title: "Use Cases",
    description: "Concrete examples of how the platform is used in personal projects and manufacturing SMBs.",
    filePath: path.resolve(process.cwd(), "..", "..", "docs", "use-cases.md"),
  },
  {
    slug: "platform-logic",
    title: "Platform Logic Guide",
    description: "How the platform works internally and how data flows.",
    filePath: path.resolve(process.cwd(), "..", "..", "docs", "platform-logic.md"),
  },
  {
    slug: "target-architecture",
    title: "Target Architecture",
    description: "The intended next architecture layer and domain evolution.",
    filePath: path.resolve(process.cwd(), "..", "..", "docs", "target-architecture.md"),
  },
  {
    slug: "implementation-backlog",
    title: "Implementation Backlog",
    description: "Planned epics and stories.",
    filePath: path.resolve(process.cwd(), "..", "..", "docs", "implementation-backlog.md"),
  },
  {
    slug: "gap-analysis",
    title: "Gap Analysis",
    description: "Current capability map and open gaps.",
    filePath: path.resolve(process.cwd(), "..", "..", "docs", "gap-analysis.md"),
  },
];

export function getDocEntry(slug: string): DocEntry | undefined {
  return DOCS.find((doc) => doc.slug === slug);
}

export async function readDoc(slug: string): Promise<{ entry: DocEntry; content: string }> {
  const entry = getDocEntry(slug);
  if (!entry) {
    throw new Error(`Unknown documentation page: ${slug}`);
  }
  const content = await fs.readFile(entry.filePath, "utf8");
  return { entry, content };
}
