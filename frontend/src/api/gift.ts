import axios from 'axios'
import type { Gift, GiftFormData, GiftStats, GiftSummary } from '../types/gift'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

export interface GiftQueryParams {
  item_name?: string
  is_taken?: number | ''
}

/** 获取全部赠送记录 */
export async function fetchGifts(params?: GiftQueryParams): Promise<Gift[]> {
  const { data } = await api.get<Gift[]>('/gifts', { params })
  return data
}

/** 新建赠送记录 */
export async function createGift(payload: GiftFormData): Promise<Gift> {
  const { data } = await api.post<Gift>('/gifts', payload)
  return data
}

/** 更新赠送记录 */
export async function updateGift(id: number, payload: GiftFormData): Promise<Gift> {
  const { data } = await api.put<Gift>(`/gifts/${id}`, payload)
  return data
}

/** 删除赠送记录 */
export async function deleteGift(id: number): Promise<void> {
  await api.delete(`/gifts/${id}`)
}

/** 快捷标记为已取走 */
export async function markGiftTaken(id: number): Promise<Gift> {
  const { data } = await api.put<Gift>(`/gifts/${id}/mark-taken`)
  return data
}

/** 获取赠送统计数据 */
export async function fetchGiftStats(): Promise<GiftStats> {
  const { data } = await api.get<GiftStats>('/stats/gifts')
  return data
}

/** 获取轻量汇总统计（总记录数、已取走数、待取走数） */
export async function fetchGiftSummary(): Promise<GiftSummary> {
  const { data } = await api.get<GiftSummary>('/gifts/summary')
  return data
}

/** 导出赠送记录为CSV文件 */
export async function exportGifts(params?: GiftQueryParams): Promise<Blob> {
  const { data } = await api.get('/gifts/export', {
    params,
    responseType: 'blob',
  })
  return data
}
