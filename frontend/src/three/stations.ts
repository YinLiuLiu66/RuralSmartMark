export type Vec3 = [number, number, number];

export interface StationMeta {
  id: string;
  name: string;
  color: string;
  position: Vec3;
}

export const STATIONS: StationMeta[] = [
  { id: "story", name: "故事馆", color: "#C9A46A", position: [-9, 0, 1] },
  { id: "packaging", name: "包装工坊", color: "#B6402A", position: [0, 0, 4] },
  { id: "marketing", name: "内容工坊", color: "#3F6B4F", position: [8, 0, 0] },
  { id: "warehouse", name: "云仓 / 门店", color: "#8A8578", position: [14, 0, 5] },
];
