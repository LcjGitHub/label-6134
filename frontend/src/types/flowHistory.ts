export type FlowActionType = 'create' | 'edit' | 'mark_taken' | 'cancel_reservation'

export interface FlowHistory {
  id: number
  gift_id: number
  action_type: FlowActionType
  operator_nickname: string
  operated_at: string
  description: string
}
