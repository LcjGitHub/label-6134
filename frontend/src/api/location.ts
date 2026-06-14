import axios from 'axios'
import type { Location, LocationFormData } from '../types/location'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

export async function fetchLocations(): Promise<Location[]> {
  const { data } = await api.get<Location[]>('/locations')
  return data
}

export async function createLocation(payload: LocationFormData): Promise<Location> {
  const { data } = await api.post<Location>('/locations', payload)
  return data
}

export async function updateLocation(
  id: number,
  payload: LocationFormData,
): Promise<Location> {
  const { data } = await api.put<Location>(`/locations/${id}`, payload)
  return data
}

export async function deleteLocation(id: number): Promise<void> {
  await api.delete(`/locations/${id}`)
}
