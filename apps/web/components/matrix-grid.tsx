"use client";

import { useMemo, useState } from "react";
import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { Badge, Card, CardBody, CardHeader } from "@/components/ui";
import type { MatrixResponse } from "@/lib/types";

export function MatrixGrid({ data }: { data: MatrixResponse }) {
  const [selected, setSelected] = useState<{ row: string; column: string; relations: string[] } | null>(null);

  const columns = useMemo<ColumnDef<any>[]>(
    () => [
      {
        accessorKey: "requirement",
        header: "Requirement",
        cell: ({ row }) => (
          <div>
            <div className="font-medium">{row.original.requirement.key}</div>
            <div className="text-xs text-muted">{row.original.requirement.title}</div>
          </div>
        ),
      },
      ...data.columns.map((column) => ({
        id: column.object_id,
        header: (
          <div className="min-w-28 text-left">
            <div className="font-medium">{column.code || column.label}</div>
            <div className="text-xs text-muted">{column.label}</div>
          </div>
        ),
        cell: ({ row }: any) => {
          const cell = data.cells.find((item) => item.row_requirement_id === row.original.requirement.id && item.column_object_id === column.object_id);
          const linked = cell?.linked;
          return (
            <button
              type="button"
              onClick={() => setSelected({ row: row.original.requirement.key, column: column.code || column.label, relations: cell?.relation_types || [] })}
              className={`h-10 w-full rounded-lg border transition ${linked ? "border-accent bg-accent/15" : "border-line bg-panel2 hover:border-accent/40"}`}
            >
              {linked ? <span className="text-xs font-semibold text-accent">linked</span> : <span className="text-xs text-muted">-</span>}
            </button>
          );
        },
      })) as any,
    ],
    [data]
  );

  const table = useReactTable({ data: data.rows, columns, getCoreRowModel: getCoreRowModel() });

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_320px]">
      <Card className="overflow-hidden">
        <CardHeader>
          <div className="flex items-center justify-between gap-4">
            <div className="font-semibold">Traceability matrix</div>
            <Badge tone="accent">{data.mode}</Badge>
          </div>
        </CardHeader>
        <CardBody className="overflow-x-auto p-0">
          <table className="min-w-full border-separate border-spacing-0 text-sm">
            <thead>
              {table.getHeaderGroups().map((headerGroup) => (
                <tr key={headerGroup.id}>
                  {headerGroup.headers.map((header) => (
                    <th key={header.id} className="sticky top-0 border-b border-line bg-panel px-4 py-3 text-left text-xs uppercase tracking-[0.2em] text-muted">
                      {flexRender(header.column.columnDef.header, header.getContext())}
                    </th>
                  ))}
                </tr>
              ))}
            </thead>
            <tbody>
              {table.getRowModel().rows.map((row) => (
                <tr key={row.id} className="border-b border-line">
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="border-b border-line px-4 py-3 align-top">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <div className="font-semibold">Cell details</div>
        </CardHeader>
        <CardBody>
          {selected ? (
            <div className="space-y-3">
              <div>
                <div className="text-xs uppercase tracking-[0.2em] text-muted">Requirement</div>
                <div className="mt-1 font-medium">{selected.row}</div>
              </div>
              <div>
                <div className="text-xs uppercase tracking-[0.2em] text-muted">Column</div>
                <div className="mt-1 font-medium">{selected.column}</div>
              </div>
              <div>
                <div className="text-xs uppercase tracking-[0.2em] text-muted">Relations</div>
                <div className="mt-2 flex flex-wrap gap-2">
                  {selected.relations.length ? selected.relations.map((rel) => <Badge key={rel}>{rel}</Badge>) : <span className="text-sm text-muted">No direct link in this cell.</span>}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-sm text-muted">Click a matrix cell to inspect the linked object relationship.</div>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
