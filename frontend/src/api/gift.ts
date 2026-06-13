import axios from 'axios'
import type { Gift, GiftFormData, GiftStats } from '../types/gift'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

/** 获取全部赠送记录 */
export async function fetchGifts(): Promise<Gift[]> {
  const { data } = await api.get<Gift[]>('/gifts')
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

/** 获取赠送统计数据 */
export async function fetchGiftStats(): Promise<GiftStats> {
  const { data } = await api.get<GiftStats>('/stats/gifts')
  return data
}
