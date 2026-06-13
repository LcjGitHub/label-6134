import axios from 'axios'
import type { GiftNote } from '../types/note'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

/** 获取指定赠送记录的备注列表 */
export async function fetchGiftNotes(giftId: number): Promise<GiftNote[]> {
  const { data } = await api.get<GiftNote[]>(`/gifts/${giftId}/notes`)
  return data
}

/** 新增备注 */
export async function createGiftNote(giftId: number, content: string): Promise<GiftNote> {
  const { data } = await api.post<GiftNote>(`/gifts/${giftId}/notes`, { content })
  return data
}
