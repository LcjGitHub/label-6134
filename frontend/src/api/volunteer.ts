import axios from 'axios'
import type { Volunteer, VolunteerFormData } from '../types/volunteer'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

export interface VolunteerQueryParams {
  name?: string
  is_active?: number | ''
}

/** 获取全部志愿者列表 */
export async function fetchVolunteers(params?: VolunteerQueryParams): Promise<Volunteer[]> {
  const { data } = await api.get<Volunteer[]>('/volunteers', { params })
  return data
}

/** 获取单个志愿者详情 */
export async function fetchVolunteer(id: number): Promise<Volunteer> {
  const { data } = await api.get<Volunteer>(`/volunteers/${id}`)
  return data
}

/** 新建志愿者 */
export async function createVolunteer(payload: VolunteerFormData): Promise<Volunteer> {
  const { data } = await api.post<Volunteer>('/volunteers', payload)
  return data
}

/** 更新志愿者 */
export async function updateVolunteer(id: number, payload: VolunteerFormData): Promise<Volunteer> {
  const { data } = await api.put<Volunteer>(`/volunteers/${id}`, payload)
  return data
}

/** 删除志愿者 */
export async function deleteVolunteer(id: number): Promise<void> {
  await api.delete(`/volunteers/${id}`)
}
