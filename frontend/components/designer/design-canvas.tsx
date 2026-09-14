"use client";

import { memo, useRef, useState } from "react";
import { Stage, Layer, Rect, Text, Group } from "react-konva";
import { faNumber } from "@/lib/format";

export interface CabinetLike {
  id?: string;
  type?: string;
  width_mm: number;
  height_mm: number;
  depth_mm: number;
  x: number;
  y: number;
  z?: number;
  rotation?: number;
  name?: string;
  material_name?: string;
}
export interface ApplianceLike {
  id?: string;
  appliance_type?: string;
  width_mm: number;
  height_mm: number;
  depth_mm: number;
  x: number;
  y: number;
  z?: number;
  rotation?: number;
  name?: string;
}

export interface CountertopLike {
  id?: string;
  width_mm: number;
  depth_mm: number;
  x: number;
  y: number;
  material_name?: string;
}

export interface DesignView {
  room: { width_mm: number; length_mm: number; height_mm: number };
  cabinets: CabinetLike[];
  appliances: ApplianceLike[];
  countertops: CountertopLike[];
  layout?: string;
}

const SCALE = 0.12; // px per mm
const PAD = 60;

// wall -> visual color
const CAB_COLORS: Record<string, string> = {
  base: "#d9c9a3",
  drawer: "#c9b98f",
  wall: "#e8e2d2",
  tall: "#b3a684",
  corner: "#d9c9a3",
  sink: "#cfe3f5",
  oven: "#8f9aa8",
  fridge: "#aab6c2",
  island: "#d9c9a3",
  peninsula: "#d9c9a3",
};

function footprint(w: number, d: number, rot: number = 0) {
  if (rot === 90 || rot === 270) return [d, w];
  return [w, d];
}

// Mirrors backend app/design/cabinet_types label_prefix per cabinet type.
const LABEL_PREFIX: Record<string, string> = {
  base: "B", corner: "B", drawer: "B", filler: "F", island: "I", microwave: "W",
  oven: "T", sink: "B", tall: "T", vanity: "V", wall: "W", fridge: "T", hood: "W",
};

export function cabinetLabels(cabinets: CabinetLike[]): Record<string, string> {
  const counters: Record<string, number> = {};
  const out: Record<string, string> = {};
  for (const c of cabinets) {
    const prefix = LABEL_PREFIX[c.type || "base"] || "K";
    counters[prefix] = (counters[prefix] || 0) + 1;
    if (c.id) out[c.id] = `${prefix}${counters[prefix]}`;
  }
  return out;
}

function DesignCanvasInner({
  design,
  onEdit,
  selectedId,
  onSelect,
}: {
  design: DesignView;
  onEdit?: (cab: CabinetLike) => void;
  selectedId?: string | null;
  onSelect?: (id: string) => void;
}) {
  const stageRef = useRef<any>(null);
  const [zoom, setZoom] = useState(1);

  const W = design.room.width_mm * SCALE;
  const L = design.room.length_mm * SCALE;
  const labels = cabinetLabels(design.cabinets);

  // Mouse-wheel zoom centered on the cursor (clamped 0.4x–3x).
  function onWheel(e: any) {
    e.evt.preventDefault();
    const stage = stageRef.current;
    if (!stage) return;
    const oldScale = stage.scaleX();
    const pointer = stage.getPointerPosition();
    if (!pointer) return;
    const direction = e.evt.deltaY > 0 ? -1 : 1;
    const factor = 1.06;
    const nextScale = Math.max(0.4, Math.min(3, oldScale * (direction > 0 ? factor : 1 / factor)));
    const mousePointTo = {
      x: (pointer.x - stage.x()) / oldScale,
      y: (pointer.y - stage.y()) / oldScale,
    };
    stage.scale({ x: nextScale, y: nextScale });
    stage.position({
      x: pointer.x - mousePointTo.x * nextScale,
      y: pointer.y - mousePointTo.y * nextScale,
    });
    setZoom(nextScale);
  }

  // Drag the room floor (empty area) to pan the stage.
  function onFloorDragEnd(e: any) {
    const stage = stageRef.current;
    if (!stage) return;
    stage.position({
      x: stage.x() + e.target.x() - PAD,
      y: stage.y() + e.target.y() - PAD,
    });
    e.target.position({ x: PAD, y: PAD });
  }

  return (
    <div className="overflow-auto rounded-xl border border-border bg-muted/30">
      <Stage
        ref={stageRef}
        width={W + PAD * 2}
        height={L + PAD * 2}
        scaleX={1}
        scaleY={1}
        onWheel={onWheel}
        className="cursor-default"
      >
        <Layer perfectDrawEnabled={false}>
          {/* room floor (draggable to pan) */}
          <Rect
            x={PAD}
            y={PAD}
            width={W}
            height={L}
            fill="#fdfcf9"
            stroke="#c9c2b6"
            strokeWidth={2}
            draggable
            onDragEnd={onFloorDragEnd}
          />
          {/* wall labels */}
          <Text x={PAD + W / 2 - 12} y={PAD - 22} text="شمال" fontSize={12} fill="#888" />
          <Text x={PAD + W / 2 - 12} y={PAD + L + 8} text="جنوب" fontSize={12} fill="#888" />
          <Text x={PAD - 40} y={PAD + L / 2 - 6} text="غرب" fontSize={12} fill="#888" />
          <Text x={PAD + W + 12} y={PAD + L / 2 - 6} text="شرق" fontSize={12} fill="#888" />

          {/* countertops */}
          {design.countertops.map((ct, i) => (
            <Rect
              key={`ct-${i}`}
              x={PAD + ct.x * SCALE}
              y={PAD + ct.y * SCALE}
              width={ct.width_mm * SCALE}
              height={ct.depth_mm * SCALE}
              fill="#8a7f66"
              opacity={0.35}
              cornerRadius={2}
            />
          ))}

          {/* cabinets */}
          {design.cabinets.map((c, i) => {
            const [fw, fd] = footprint(c.width_mm, c.depth_mm, c.rotation);
            const color = CAB_COLORS[c.type || "base"] || CAB_COLORS.base;
            const isWall = c.type === "wall";
            const selected = selectedId === c.id;
            return (
              <Group
                key={`cab-${i}`}
                x={PAD + c.x * SCALE}
                y={PAD + c.y * SCALE}
                perfectDrawEnabled={false}
                onClick={(e) => {
                  e.cancelBubble = true;
                  if (onSelect && c.id) onSelect(c.id);
                }}
                draggable={!!onEdit && !isWall}
                onDragEnd={(e) => {
                  if (onEdit && c.id) {
                    onEdit({
                      ...c,
                      x: (e.target.x() - PAD) / SCALE,
                      y: (e.target.y() - PAD) / SCALE,
                    });
                  }
                }}
              >
                <Rect
                  width={fw * SCALE}
                  height={fd * SCALE}
                  fill={color}
                  stroke={selected ? "#b8893c" : "#7a6f57"}
                  strokeWidth={selected ? 2.5 : 1.2}
                  cornerRadius={2}
                  shadowColor="#00000022"
                  shadowBlur={4}
                />
                <Text
                  x={2}
                  y={2}
                  width={fw * SCALE - 4}
                  height={fd * SCALE - 4}
                  text={`${c.id && labels[c.id] ? labels[c.id] + " · " : ""}${c.name || "کابینت"}`}
                  fontSize={fw > 120 ? 9 : 7}
                  fill="#3a332a"
                  align="center"
                  verticalAlign="middle"
                  ellipsis
                />
              </Group>
            );
          })}

          {/* appliances (smaller markers over cabinets) */}
          {design.appliances.map((a, i) => {
            const [fw, fd] = footprint(a.width_mm, a.depth_mm, a.rotation);
            const colors: Record<string, string> = {
              sink: "#5b93c9",
              cooktop: "#d98c3f",
              oven: "#6b7686",
              fridge: "#9fb0c0",
              dishwasher: "#7d93a8",
              hood: "#a09a8e",
              faucet: "#8f8f8f",
            };
            return (
              <Group key={`ap-${i}`} x={PAD + a.x * SCALE} y={PAD + a.y * SCALE}>
                <Rect
                  width={fw * SCALE}
                  height={fd * SCALE}
                  fill={colors[a.appliance_type || ""] || "#999"}
                  opacity={0.85}
                  cornerRadius={2}
                />
                <Text
                  x={1}
                  y={1}
                  width={fw * SCALE - 2}
                  height={fd * SCALE - 2}
                  text={a.name || a.appliance_type || ""}
                  fontSize={fw > 100 ? 8 : 6}
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
      <div className="flex items-center justify-between px-3 py-2 text-xs text-muted-foreground">
        <span>
          ابعاد فضا: {faNumber(design.room.width_mm)}×{faNumber(design.room.length_mm)} میلی‌متر
        </span>
        <span className="flex items-center gap-3">
          <span>بزرگنمایی: {faNumber(Math.round(zoom * 100))}٪</span>
          <span>برای جابجایی کابینت‌ها روی آن‌ها بکشید · چرخ ماوس برای زوم</span>
        </span>
      </div>
    </div>
  );
}

export const DesignCanvas = memo(DesignCanvasInner);
