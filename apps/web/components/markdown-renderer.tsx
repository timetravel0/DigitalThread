import { ReactNode } from "react";

function escapeHtml(value: string): string {
  return value
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

function renderInline(value: string): string {
  const escaped = escapeHtml(value);
  return escaped
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`(.+?)`/g, "<code>$1</code>")
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a class="text-accent underline decoration-accent/40 underline-offset-2 hover:decoration-accent" href="$2" target="_blank" rel="noreferrer">$1</a>');
}

function isSeparatorRow(line: string): boolean {
  return /^\s*\|?(?:\s*:?-{3,}:?\s*\|)+\s*:?-{3,}:?\s*\|?\s*$/.test(line);
}

function parseTable(rows: string[]): string {
  const cleaned = rows.filter((row) => row.trim().length > 0 && !isSeparatorRow(row));
  if (!cleaned.length) return "";
  const cells = cleaned.map((row) =>
    row
      .trim()
      .replace(/^\|/, "")
      .replace(/\|$/, "")
      .split("|")
      .map((cell) => cell.trim())
  );
  const header = cells[0];
  const body = cells.slice(1);
  const headHtml = `<tr>${header.map((cell) => `<th class="border border-line bg-white/5 px-3 py-2 text-left text-xs font-semibold uppercase tracking-[0.2em] text-muted">${renderInline(cell)}</th>`).join("")}</tr>`;
  const bodyHtml = body
    .map(
      (row) =>
        `<tr>${row.map((cell) => `<td class="border border-line px-3 py-2 align-top text-sm text-text">${renderInline(cell)}</td>`).join("")}</tr>`
    )
    .join("");
  return `<div class="overflow-x-auto rounded-2xl border border-line bg-panel"><table class="min-w-full border-collapse">${headHtml}${bodyHtml}</table></div>`;
}

function flushParagraph(lines: string[]): string {
  if (!lines.length) return "";
  return `<p class="leading-7 text-text">${renderInline(lines.join(" ").trim())}</p>`;
}

function flushList(items: string[], ordered: boolean): string {
  if (!items.length) return "";
  const tag = ordered ? "ol" : "ul";
  const className = ordered ? "list-decimal" : "list-disc";
  return `<${tag} class="${className} ml-6 space-y-2">${items.map((item) => `<li class="leading-7">${renderInline(item)}</li>`).join("")}</${tag}>`;
}

function flushBlockquote(lines: string[]): string {
  if (!lines.length) return "";
  return `<blockquote class="border-l-4 border-accent/40 bg-accent/5 px-4 py-3 text-sm text-muted">${lines.map((line) => `<p class="leading-7">${renderInline(line)}</p>`).join("")}</blockquote>`;
}

function flushCode(lines: string[], language: string): string {
  const className = language ? `language-${escapeHtml(language)}` : "";
  return `<pre class="overflow-x-auto rounded-2xl border border-line bg-slate-950/80 p-4 text-sm text-slate-100"><code class="${className}">${escapeHtml(lines.join("\n"))}</code></pre>`;
}

function flushTable(rows: string[]): string {
  if (!rows.length) return "";
  return parseTable(rows);
}

export function MarkdownRenderer({ content }: { content: string }) {
  const html = renderMarkdown(content);
  return <div className="docs-markdown space-y-5 text-sm text-text" dangerouslySetInnerHTML={{ __html: html }} />;
}

function renderMarkdown(markdown: string): string {
  const lines = markdown.replaceAll("\r\n", "\n").split("\n");
  const chunks: string[] = [];
  let paragraph: string[] = [];
  let listItems: string[] = [];
  let orderedListItems: string[] = [];
  let quoteLines: string[] = [];
  let tableRows: string[] = [];
  let codeLines: string[] = [];
  let inCode = false;
  let codeLanguage = "";

  const flushAll = () => {
    chunks.push(flushParagraph(paragraph));
    paragraph = [];
    chunks.push(flushList(listItems, false));
    listItems = [];
    chunks.push(flushList(orderedListItems, true));
    orderedListItems = [];
    chunks.push(flushBlockquote(quoteLines));
    quoteLines = [];
    chunks.push(flushTable(tableRows));
    tableRows = [];
  };

  for (const rawLine of lines) {
    const line = rawLine.replace(/\s+$/, "");

    if (inCode) {
      if (line.trim().startsWith("```")) {
        chunks.push(flushCode(codeLines, codeLanguage));
        codeLines = [];
        inCode = false;
        codeLanguage = "";
      } else {
        codeLines.push(rawLine);
      }
      continue;
    }

    if (line.trim().startsWith("```")) {
      flushAll();
      inCode = true;
      codeLanguage = line.trim().slice(3).trim();
      continue;
    }

    if (!line.trim()) {
      flushAll();
      continue;
    }

    const heading = /^(#{1,6})\s+(.*)$/.exec(line);
    if (heading) {
      flushAll();
      const level = heading[1].length;
      const sizes = {
        1: "text-3xl",
        2: "text-2xl",
        3: "text-xl",
        4: "text-lg",
        5: "text-base",
        6: "text-sm",
      } as const;
      chunks.push(`<h${level} class="${sizes[level as keyof typeof sizes]} font-semibold tracking-tight text-text">${renderInline(heading[2])}</h${level}>`);
      continue;
    }

    if (/^\s*>\s?/.test(line)) {
      chunks.push(flushParagraph(paragraph));
      paragraph = [];
      chunks.push(flushList(listItems, false));
      listItems = [];
      chunks.push(flushList(orderedListItems, true));
      orderedListItems = [];
      chunks.push(flushTable(tableRows));
      tableRows = [];
      quoteLines.push(line.replace(/^\s*>\s?/, ""));
      continue;
    }

    const unordered = /^\s*[-*]\s+(.*)$/.exec(line);
    if (unordered) {
      chunks.push(flushParagraph(paragraph));
      paragraph = [];
      chunks.push(flushList(orderedListItems, true));
      orderedListItems = [];
      chunks.push(flushBlockquote(quoteLines));
      quoteLines = [];
      chunks.push(flushTable(tableRows));
      tableRows = [];
      listItems.push(unordered[1]);
      continue;
    }

    const ordered = /^\s*\d+\.\s+(.*)$/.exec(line);
    if (ordered) {
      chunks.push(flushParagraph(paragraph));
      paragraph = [];
      chunks.push(flushList(listItems, false));
      listItems = [];
      chunks.push(flushBlockquote(quoteLines));
      quoteLines = [];
      chunks.push(flushTable(tableRows));
      tableRows = [];
      orderedListItems.push(ordered[1]);
      continue;
    }

    if (line.includes("|")) {
      chunks.push(flushParagraph(paragraph));
      paragraph = [];
      chunks.push(flushList(listItems, false));
      listItems = [];
      chunks.push(flushList(orderedListItems, true));
      orderedListItems = [];
      chunks.push(flushBlockquote(quoteLines));
      quoteLines = [];
      tableRows.push(line);
      continue;
    }

    chunks.push(flushList(listItems, false));
    listItems = [];
    chunks.push(flushList(orderedListItems, true));
    orderedListItems = [];
    chunks.push(flushBlockquote(quoteLines));
    quoteLines = [];
    chunks.push(flushTable(tableRows));
    tableRows = [];
    paragraph.push(line);
  }

  if (inCode) {
    chunks.push(flushCode(codeLines, codeLanguage));
  }
  chunks.push(flushParagraph(paragraph));
  chunks.push(flushList(listItems, false));
  chunks.push(flushList(orderedListItems, true));
  chunks.push(flushBlockquote(quoteLines));
  chunks.push(flushTable(tableRows));

  return chunks.filter(Boolean).join("\n");
}
