export interface GiftNote {
  id: number
  gift_id: number
  content: string
  created_at: string
}

export interface GiftNoteFormData {
  content: string
}
