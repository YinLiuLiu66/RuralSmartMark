// M0 探针：站点与假数据全部硬编码，M3 正式化后由 REST 快照 + WS 供数
export interface SiteInfo {
  pallets: number
  tempZone: string
  throughput: string
  note: string
}

export interface SiteData {
  id: string
  name: string
  color: string
  /** 地面锚点（x, y 固定 0, z），方块在上方立起 */
  position: [number, number, number]
  info: SiteInfo
}

export const SITES: SiteData[] = [
  {
    id: 'farm',
    name: '高山蓝莓农场 · 产地',
    color: '#6aa84f',
    position: [-7, 0, -1.5],
    info: {
      pallets: 24,
      tempZone: '常温（待预冷）',
      throughput: '今晨采摘 12 托',
      note: '今日可采 40 托，果径 14mm+，糖度 12.4%',
    },
  },
  {
    id: 'hub',
    name: '县集货仓 · 分拣包装',
    color: '#d97706',
    position: [0, 0, 1.8],
    info: {
      pallets: 18,
      tempZone: '冷藏 0–4℃',
      throughput: '入库 9 托 / 礼盒装 5 托',
      note: '文创礼盒码托 5 托待出库',
    },
  },
  {
    id: 'depot',
    name: '城市前置仓',
    color: '#0ea5e9',
    position: [7, 0, -1.2],
    info: {
      pallets: 9,
      tempZone: '冷藏 0–4℃',
      throughput: '补货 4 托 / 出库 3 托',
      note: '安全水位 4 托，当前高于阈值',
    },
  },
  {
    id: 'market',
    name: '消费端 · 礼盒门店',
    color: '#8b5cf6',
    position: [13, 0, 1.2],
    info: {
      pallets: 6,
      tempZone: '冷藏陈列',
      throughput: '今日售出礼盒 42 盒',
      note: '扫码溯源打开率 68%',
    },
  },
]
