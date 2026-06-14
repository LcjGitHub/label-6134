import axios from 'axios'
import type { FlowHistory } from '../types/flowHistory'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

export async function fetchFlowHistory(giftId: number): Promise<FlowHistory[]> {
  const { data } = await api.get<FlowHistory[]>(`/gifts/${giftId}/flow-history`)
  return data
}
