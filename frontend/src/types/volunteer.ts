export interface Volunteer {
  id: number
  name: string
  phone: string
  service_time: string
  skill_category: string
  register_date: string
  is_active: boolean
}

export interface VolunteerFormData {
  name: string
  phone: string
  service_time: string
  skill_category: string
  register_date: string
  is_active: boolean
}
