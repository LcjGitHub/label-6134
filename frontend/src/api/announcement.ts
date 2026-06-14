import axios from 'axios'
import type { Announcement, AnnouncementFormData } from '../types/announcement'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

export interface AnnouncementQueryParams {
  title?: string
  is_pinned?: number | ''
}

/** 获取全部公告列表 */
export async function fetchAnnouncements(params?: AnnouncementQueryParams): Promise<Announcement[]> {
  const { data } = await api.get<Announcement[]>('/announcements', { params })
  return data
}

/** 获取单个公告详情 */
export async function fetchAnnouncement(id: number): Promise<Announcement> {
  const { data } = await api.get<Announcement>(`/announcements/${id}`)
  return data
}

/** 新建公告 */
export async function createAnnouncement(payload: AnnouncementFormData): Promise<Announcement> {
  const { data } = await api.post<Announcement>('/announcements', payload)
  return data
}

/** 更新公告 */
export async function updateAnnouncement(id: number, payload: AnnouncementFormData): Promise<Announcement> {
  const { data } = await api.put<Announcement>(`/announcements/${id}`, payload)
  return data
}

/** 切换公告置顶状态 */
export async function toggleAnnouncementPin(id: number): Promise<Announcement> {
  const { data } = await api.put<Announcement>(`/announcements/${id}/toggle-pin`)
  return data
}

/** 删除公告 */
export async function deleteAnnouncement(id: number): Promise<void> {
  await api.delete(`/announcements/${id}`)
}
