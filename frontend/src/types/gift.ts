/** 赠送记录实体 */
export interface Gift {
  id: number
  item_name: string
  description: string
  gift_date: string
  recipient_nickname: string
  is_taken: boolean
}

/** 创建/更新赠送记录时的表单数据 */
export interface GiftFormData {
  item_name: string
  description: string
  gift_date: string
  recipient_nickname: string
  is_taken: boolean
}
