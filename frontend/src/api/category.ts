import axios from 'axios'
import type { Category, CategoryFormData } from '../types/category'

const api = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

export async function fetchCategories(): Promise<Category[]> {
  const { data } = await api.get<Category[]>('/categories')
  return data
}

export async function createCategory(payload: CategoryFormData): Promise<Category> {
  const { data } = await api.post<Category>('/categories', payload)
  return data
}

export async function updateCategory(
  id: number,
  payload: CategoryFormData,
): Promise<Category> {
  const { data } = await api.put<Category>(`/categories/${id}`, payload)
  return data
}

export async function deleteCategory(id: number): Promise<void> {
  await api.delete(`/categories/${id}`)
}
