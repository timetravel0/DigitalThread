import Link from "next/link";
import { notFound } from "next/navigation";
import { MarkdownRenderer } from "@/components/markdown-renderer";
import { Button, Card, CardBody, CardHeader, SectionTitle } from "@/components/ui";
import { DOCS, readDoc } from "@/lib/docs";

export const dynamic = "force-dynamic";

export function generateStaticParams() {
  return DOCS.map((doc) => ({ slug: doc.slug }));
}

export default async function DocumentationPage({ params }: { params: { slug: string } }) {
  const doc = DOCS.find((item) => item.slug === params.slug);
  if (!doc) {
    notFound();
  }

  const { content } = await readDoc(params.slug);

  return (
    <div className="space-y-6">
      <SectionTitle
        title={doc.title}
        description={doc.description}
        action={<Button href="/docs" variant="secondary">Back to documentation</Button>}
      />
      <div className="grid gap-6 xl:grid-cols-[280px_1fr]">
        <Card className="h-fit">
          <CardHeader>
            <div className="font-semibold">Manual sections</div>
          </CardHeader>
          <CardBody className="space-y-2">
            {DOCS.map((item) => (
              <Link
                key={item.slug}
                href={`/docs/${item.slug}`}
                className={`block rounded-xl border px-3 py-2 text-sm transition ${
                  item.slug === doc.slug ? "border-accent bg-accent/10 text-accent" : "border-transparent text-text hover:bg-white/5"
                }`}
              >
                <div className="font-medium">{item.title}</div>
                <div className="text-xs text-muted">{item.description}</div>
              </Link>
            ))}
          </CardBody>
        </Card>

        <Card>
          <CardHeader>
            <div className="font-semibold">{doc.title}</div>
          </CardHeader>
          <CardBody>
            <MarkdownRenderer content={content} />
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
