export type ReservationStatus = 'pending' | 'confirmed' | 'cancelled'

export interface Reservation {
  id: number
  gift_id: number
  gift_item_name: string | null
  reserver_nickname: string
  reserve_time: string
  status: ReservationStatus
}

export interface ReservationFormData {
  gift_id: number | null
  reserver_nickname: string
  reserve_time: string
  status: ReservationStatus
}
