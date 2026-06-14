export interface Announcement {
  id: number
  title: string
  content: string
  publisher_nickname: string
  publish_time: string
  is_pinned: boolean
}

export interface AnnouncementFormData {
  title: string
  content: string
  publisher_nickname: string
  publish_time: string
  is_pinned: boolean
}
