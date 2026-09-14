"use client";

// 2D spatial editor — place objects (fridge, sink, dishwasher, island, ...)
// onto the room footprint. Each object produces an ObjectPosition with a
// wall + along-wall offset, matching the KitchenSpecification schema.

import { useState } from "react";
import { Stage, Layer, Rect, Text, Group } from "react-konva";
import { faNumber } from "@/lib/format";
import type { ObjectPosition, WallSide } from "@/lib/ai-spec";

const SCALE = 0.12;
const PAD = 60;

export const OBJECT_TYPES: { type: string; fa: string; w: number; d: number; h?: number }[] = [
  { type: "refrigerator", fa: "یخچال", w: 700, d: 700, h: 1780 },
  { type: "dishwasher", fa: "ظرف‌شویی", w: 600, d: 600, h: 820 },
  { type: "washing_machine", fa: "لباسشویی", w: 600, d: 600, h: 850 },
  { type: "oven", fa: "فر", w: 600, d: 600, h: 600 },
  { type: "cooktop", fa: "اجاق گاز", w: 600, d: 520, h: 60 },
  { type: "hood", fa: "هود", w: 600, d: 350, h: 300 },
  { type: "island", fa: "جزیره", w: 1500, d: 900, h: 900 },
];

const OBJECT_FA: Record<string, string> = Object.fromEntries(
  OBJECT_TYPES.map((o) => [o.type, o.fa]),
);

interface WallGeom {
  start: number;
  end: number;
  fixed: number;
  labelX: number;
  labelY: number;
}

function wallGeom(side: WallSide, W: number, L: number): WallGeom {
  switch (side) {
    case "north":
      return { start: PAD, end: PAD + W, fixed: PAD, labelX: PAD + W / 2 - 12, labelY: PAD - 34 };
    case "south":
      return { start: PAD, end: PAD + W, fixed: PAD + L, labelX: PAD + W / 2 - 12, labelY: PAD + L + 10 };
    case "west":
      return { start: PAD, end: PAD + L, fixed: PAD, labelX: PAD - 46, labelY: PAD + L / 2 - 6 };
    case "east":
      return { start: PAD, end: PAD + L, fixed: PAD + W, labelX: PAD + W + 14, labelY: PAD + L / 2 - 6 };
  }
}

function isHorizontal(side: WallSide): boolean {
  return side === "north" || side === "south";
}

export function SpatialEditor({
  width,
  length,
  objects,
  onChange,
}: {
  width: number;
  length: number;
  objects: ObjectPosition[];
  onChange: (objects: ObjectPosition[]) => void;
}) {
  const [active, setActive] = useState<string>("refrigerator");

  const W = width * SCALE;
  const L = length * SCALE;

  function handleWallClick(side: WallSide, e: any) {
    const t = OBJECT_TYPES.find((o) => o.type === active);
    if (!t) return;
    const stage = e.target.getStage();
    const pointer = stage?.getPointerPosition();
    if (!pointer) return;

    const g = wallGeom(side, W, L);
    const alongCanvas = isHorizontal(side) ? pointer.x : pointer.y;
    let offsetMm = Math.round((alongCanvas - g.start) / SCALE);

    if (active === "island") {
      // free-standing island centered at the click point
      const maxX = width - t.w;
      const offX = Math.round((pointer.x - PAD) / SCALE) - t.w / 2;
      offsetMm = Math.max(0, Math.min(maxX, offX));
      onChange([
        ...objects,
        {
          type: t.type,
          wall: null,
          offset: offsetMm,
          width: t.w,
          depth: t.d,
          height: t.h ?? null,
          rotation: 0,
        },
      ]);
      return;
    }

    const maxOffset = (g.end - g.start) / SCALE - t.d;
    offsetMm = Math.max(0, Math.min(maxOffset, offsetMm));
    onChange([
      ...objects,
      {
        type: t.type,
        wall: side,
        offset: offsetMm,
        width: t.w,
        depth: t.d,
        height: t.h ?? null,
        rotation: 0,
      },
    ]);
  }

  function objectRect(o: ObjectPosition): { x: number; y: number; w: number; d: number } {
    const wpx = o.width * SCALE;
    const dpx = o.depth * SCALE;
    switch (o.wall) {
      case "south":
        return { x: PAD + o.offset * SCALE, y: PAD + L - dpx, w: wpx, d: dpx };
      case "west":
        return { x: PAD - wpx, y: PAD + o.offset * SCALE, w: wpx, d: dpx };
      case "east":
        return { x: PAD + W, y: PAD + o.offset * SCALE, w: wpx, d: dpx };
      default:
        return { x: PAD + o.offset * SCALE, y: PAD, w: wpx, d: dpx };
    }
  }

  function handleObjectDrag(i: number, o: ObjectPosition, e: any) {
    // Use the dragged node's own position (Konva accumulates the drag delta),
    // which is far more reliable than pointer coordinates for hit-testing.
    const g = e.target;
    const x = g.x();
    const y = g.y();
    let offsetMm: number;
    if (o.wall) {
      const horizontal = isHorizontal(o.wall);
      const wallLenMm = horizontal ? width : length;
      const maxOffset = wallLenMm - o.depth;
      // objectRect places the offset origin at PAD for every wall, so the
      // along-wall coordinate is (x-PAD) for north/south and (y-PAD) for west/east.
      const along = horizontal ? x - PAD : y - PAD;
      offsetMm = Math.max(0, Math.min(maxOffset, Math.round(along / SCALE)));
    } else {
      const maxX = width - o.width;
      const offX = Math.round((x - PAD) / SCALE) - o.width / 2;
      offsetMm = Math.max(0, Math.min(maxX, offX));
    }
    onChange(objects.map((obj, idx) => (idx === i ? { ...obj, offset: offsetMm } : obj)));
  }

  return (
    <div className="space-y-3">
      {/* palette */}
      <div className="flex flex-wrap gap-2">
        {OBJECT_TYPES.map((o) => (
          <button
            key={o.type}
            type="button"
            onClick={() => setActive(o.type)}
            className={`rounded-lg border px-3 py-1.5 text-xs transition-colors ${
              active === o.type
                ? "border-primary bg-primary/10 font-bold text-primary"
                : "border-border hover:border-primary/40"
            }`}
          >
            {o.fa}
          </button>
        ))}
      </div>

      <div className="overflow-auto rounded-xl border border-border bg-muted/30">
        <Stage width={W + PAD * 2} height={L + PAD * 2}>
          <Layer perfectDrawEnabled={false}>
            <Rect x={PAD} y={PAD} width={W} height={L} fill="#fdfcf9" stroke="#c9c2b6" strokeWidth={2} />

            {(["north", "south", "west", "east"] as WallSide[]).map((side) => {
              const g = wallGeom(side, W, L);
              const horizontal = isHorizontal(side);
              return (
                <Rect
                  key={side}
                  x={horizontal ? g.start - 10 : side === "east" ? PAD + W - 8 : PAD - 12}
                  y={horizontal ? (side === "north" ? PAD - 12 : PAD + L - 8) : g.start - 10}
                  width={horizontal ? g.end - g.start + 20 : 20}
                  height={horizontal ? 20 : g.end - g.start + 20}
                  fill="rgba(183,137,60,0.18)"
                  stroke="#b8893c"
                  strokeWidth={2}
                  onClick={(e) => handleWallClick(side, e)}
                  listening
                />
              );
            })}

            {(["north", "south", "west", "east"] as WallSide[]).map((side) => {
              const g = wallGeom(side, W, L);
              return (
                <Text
                  key={`lbl-${side}`}
                  x={g.labelX}
                  y={g.labelY}
                  text={side === "north" ? "شمال" : side === "south" ? "جنوب" : side === "west" ? "غرب" : "شرق"}
                  fontSize={12}
                  fill="#888"
                />
              );
            })}

            {objects.map((o, i) => {
              const r = objectRect(o);
              return (
                <Group
                  key={i}
                  x={r.x}
                  y={r.y}
                  draggable
                  perfectDrawEnabled={false}
                  onDragEnd={(e) => handleObjectDrag(i, o, e)}
                >
                  <Rect
                    width={r.w}
                    height={r.d}
                    fill={o.type === "island" ? "#8a7f66" : "#aab6c2"}
                    opacity={0.85}
                    stroke="#5b5340"
                    strokeWidth={1}
                    cornerRadius={2}
                  />
                  <Text
                    x={2}
                    y={2}
                    width={r.w - 4}
                    height={r.d - 4}
                    text={OBJECT_FA[o.type] || o.type}
                    fontSize={r.w > 80 ? 9 : 7}
                    fill="#fff"
                    align="center"
                    verticalAlign="middle"
                    ellipsis
                  />
                </Group>
              );
            })}
          </Layer>
        </Stage>
      </div>

      {objects.length > 0 && (
        <ul className="divide-y divide-border rounded-xl border border-border">
          {objects.map((o, i) => (
            <li key={i} className="flex items-center justify-between px-3 py-2 text-sm">
              <span>
                {OBJECT_FA[o.type] || o.type}
                {o.wall ? (
                  <span className="text-muted-foreground">
                    {" "}
                    · دیوار {o.wall} · فاصله {faNumber(o.offset)}mm
                  </span>
                ) : (
                  <span className="text-muted-foreground"> · آزاد (جزیره)</span>
                )}
              </span>
              <button
                type="button"
                onClick={() => onChange(objects.filter((_, idx) => idx !== i))}
                className="rounded-md px-2 py-0.5 text-xs text-danger hover:bg-danger/10"
              >
                حذف
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
