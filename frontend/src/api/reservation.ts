import axios from 'axios'
import type { Reservation, ReservationFormData, ReservationStatus } from '../types/reservation'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

export async function fetchReservations(status?: ReservationStatus): Promise<Reservation[]> {
  const params = status ? { status } : {}
  const { data } = await api.get<Reservation[]>('/reservations', { params })
  return data
}

export async function createReservation(payload: ReservationFormData): Promise<Reservation> {
  const { data } = await api.post<Reservation>('/reservations', payload)
  return data
}

export async function cancelReservation(id: number): Promise<Reservation> {
  const { data } = await api.put<Reservation>(`/reservations/${id}/cancel`)
  return data
}
