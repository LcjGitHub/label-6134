export interface Gift {
  id: number
  item_name: string
  description: string
  gift_date: string
  recipient_nickname: string
  is_taken: boolean
  category_id: number | null
  category_name: string | null
}

export interface GiftFormData {
  item_name: string
  description: string
  gift_date: string
  recipient_nickname: string
  is_taken: boolean
  category_id: number | null
}
