export interface Gift {
  id: number
  item_name: string
  description: string
  gift_date: string
  recipient_nickname: string
  is_taken: boolean
  category_id: number | null
  category_name: string | null
  donor_nickname: string
  donor_phone: string
  location: string
}

export interface GiftFormData {
  item_name: string
  description: string
  gift_date: string
  recipient_nickname: string
  is_taken: boolean
  category_id: number | null
  donor_nickname: string
  donor_phone: string
  location: string
}

export interface MonthlyStat {
  month: string
  count: number
}

export interface GiftStats {
  total_count: number
  taken_count: number
  pending_count: number
  monthly_stats: MonthlyStat[]
}

export interface GiftSummary {
  total_count: number
  taken_count: number
  pending_count: number
}
