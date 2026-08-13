// TypeScript KitchenSpecification — mirrors app/ai/spec.py (Pydantic).
// Units are millimetres by default. Walls: north=y=0, south=y=length,
// west=x=0, east=x=width. All positions are along-wall offsets.

export type WallSide = "north" | "south" | "east" | "west";
export type Unit = "mm" | "cm" | "m";
export type SwingDirection = "left" | "right" | "double" | "none";

export enum LayoutKind {
  SINGLE_WALL = "SINGLE_WALL",
  L_SHAPE = "L_SHAPE",
  U_SHAPE = "U_SHAPE",
  G_SHAPE = "G_SHAPE",
  ISLAND = "ISLAND",
  PENINSULA = "PENINSULA",
}

export const LAYOUT_ENGINE: Record<LayoutKind, string> = {
  [LayoutKind.SINGLE_WALL]: "linear",
  [LayoutKind.L_SHAPE]: "L",
  [LayoutKind.U_SHAPE]: "U",
  [LayoutKind.G_SHAPE]: "galley",
  [LayoutKind.ISLAND]: "island",
  [LayoutKind.PENINSULA]: "peninsula",
};

export const LAYOUT_FA: Record<LayoutKind, string> = {
  [LayoutKind.SINGLE_WALL]: "خطی (یک دیوار)",
  [LayoutKind.L_SHAPE]: "ال",
  [LayoutKind.U_SHAPE]: "یو",
  [LayoutKind.G_SHAPE]: "جی",
  [LayoutKind.ISLAND]: "جزیره",
  [LayoutKind.PENINSULA]: "شبه‌جزیره",
};

export enum StyleKind {
  MODERN = "modern",
  CLASSIC = "classic",
  MINIMAL = "minimal",
  CONTEMPORARY = "contemporary",
}

export const STYLE_FA: Record<StyleKind, string> = {
  [StyleKind.MODERN]: "مدرن",
  [StyleKind.CLASSIC]: "کلاسیک",
  [StyleKind.MINIMAL]: "مینیمال",
  [StyleKind.CONTEMPORARY]: "معاصر",
};

export interface RoomSpec {
  width: number;
  length: number;
  height: number;
  unit: Unit;
}

export interface WallSpec {
  side: WallSide;
  length: number;
  thickness?: number;
}

export interface DoorSpec {
  id?: string;
  wall: WallSide;
  offset: number;
  width: number;
  height?: number;
  swing?: SwingDirection;
}

export interface WindowSpec {
  id?: string;
  wall: WallSide;
  offset: number;
  width: number;
  height?: number;
  sill_height?: number;
}

export interface CabinetSpec {
  type: "base" | "wall" | "tall" | "corner" | "drawer";
  width: number;
  height: number;
  depth: number;
  count?: number;
}

export type ApplianceVariant =
  | "single_door"
  | "double_door"
  | "side_by_side"
  | "built_in"
  | "45cm"
  | "60cm"
  | "front_load"
  | "top_load"
  | "countertop"
  | "freestanding"
  | "wall_mounted"
  | "island";

export interface ApplianceSpec {
  type:
    | "refrigerator"
    | "dishwasher"
    | "washing_machine"
    | "oven"
    | "cooktop"
    | "hood";
  variant?: ApplianceVariant;
  width?: number;
  height?: number;
  depth?: number;
}

export interface SinkSpec {
  type: "single_bowl" | "double_bowl";
  width?: number;
  depth?: number;
}

export interface ObjectPosition {
  type: string;
  wall?: WallSide | null;
  offset: number;
  width: number;
  depth: number;
  height?: number | null;
  rotation?: number;
}

export interface ColorsSpec {
  cabinet_color: string;
  cabinet_finish: string;
  handle_style: string;
}

export interface CountertopSpec {
  material: string;
  color: string;
  thickness: number;
}

export interface PhotoSpec {
  id?: string;
  storage_key?: string;
  url?: string;
  caption?: string | null;
  content_type?: string | null;
}

export interface UserRequirements {
  notes: string;
  preferences: string[];
  must_include: string[];
  must_avoid: string[];
}

export interface KitchenSpecification {
  version: string;
  project_id: string;
  project_name: string;
  room: RoomSpec;
  walls: WallSpec[];
  doors: DoorSpec[];
  windows: WindowSpec[];
  layout: LayoutKind;
  cabinets: CabinetSpec[];
  appliances: ApplianceSpec[];
  sink: SinkSpec | null;
  objects: ObjectPosition[];
  style: StyleKind;
  colors: ColorsSpec;
  countertop: CountertopSpec;
  photos: PhotoSpec[];
  user_requirements: UserRequirements;
}

export const DEFAULT_SPEC: KitchenSpecification = {
  version: "1.0",
  project_id: "",
  project_name: "آشپزخانه",
  room: { width: 4200, length: 3600, height: 2700, unit: "mm" },
  walls: [
    { side: "north", length: 4200 },
    { side: "south", length: 4200 },
    { side: "east", length: 3600 },
    { side: "west", length: 3600 },
  ],
  doors: [],
  windows: [],
  layout: LayoutKind.L_SHAPE,
  cabinets: [
    { type: "base", width: 600, height: 720, depth: 600, count: 6 },
    { type: "wall", width: 600, height: 900, depth: 350, count: 3 },
  ],
  appliances: [
    { type: "refrigerator", variant: "double_door" },
    { type: "dishwasher", variant: "60cm" },
    { type: "cooktop", variant: "built_in" },
  ],
  sink: { type: "double_bowl", width: 900, depth: 500 },
  objects: [],
  style: StyleKind.MODERN,
  colors: { cabinet_color: "سفید", cabinet_finish: "مات", handle_style: "بدون دستگیره" },
  countertop: { material: "کوارتز", color: "سفید", thickness: 40 },
  photos: [],
  user_requirements: { notes: "", preferences: [], must_include: [], must_avoid: [] },
};

export function syncWalls(spec: KitchenSpecification): KitchenSpecification {
  const { width, length } = spec.room;
  const walls: WallSpec[] = [
    { side: "north", length: width, thickness: 150 },
    { side: "south", length: width, thickness: 150 },
    { side: "east", length: length, thickness: 150 },
    { side: "west", length: length, thickness: 150 },
  ];
  return { ...spec, walls };
}
