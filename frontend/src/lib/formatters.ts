import type {
  AssignmentStatus,
  BodyType,
  CargoStatus,
  CompanyKind,
  TruckStatus,
} from '@/types/api'

const dateTimeFmt = new Intl.DateTimeFormat('uz-UZ', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  try {
    return dateTimeFmt.format(new Date(iso))
  } catch {
    return iso
  }
}

const relFmt = new Intl.RelativeTimeFormat('uz', { numeric: 'auto' })

export function formatRelative(iso: string | null | undefined): string {
  if (!iso) return '—'
  const diffMs = new Date(iso).getTime() - Date.now()
  const diffMin = Math.round(diffMs / 60_000)
  if (Math.abs(diffMin) < 60) return relFmt.format(diffMin, 'minute')
  const diffH = Math.round(diffMin / 60)
  if (Math.abs(diffH) < 24) return relFmt.format(diffH, 'hour')
  const diffD = Math.round(diffH / 24)
  return relFmt.format(diffD, 'day')
}

export function formatWeight(kg: number): string {
  if (kg >= 1000) return `${(kg / 1000).toFixed(1)} t`
  return `${kg} kg`
}

export function formatDistance(km: number): string {
  return `${km.toFixed(1)} km`
}

export function formatNumber(n: number): string {
  return new Intl.NumberFormat('uz-UZ').format(n)
}

export const truckStatusLabel: Record<TruckStatus, string> = {
  available: 'Bo‘sh',
  busy: 'Yo‘lda',
  loading: 'Yuklanmoqda',
  unloading: 'Tushirilmoqda',
  maintenance: 'Ta’mirda',
  off_duty: 'Dam',
}

export const truckStatusColor: Record<TruckStatus, 'green' | 'blue' | 'yellow' | 'gray' | 'red'> = {
  available: 'green',
  busy: 'blue',
  loading: 'yellow',
  unloading: 'yellow',
  maintenance: 'red',
  off_duty: 'gray',
}

export const cargoStatusLabel: Record<CargoStatus, string> = {
  new: 'Yangi',
  assigned: 'Biriktirilgan',
  picked_up: 'Olingan',
  in_transit: 'Yo‘lda',
  delivered: 'Yetkazildi',
  cancelled: 'Bekor',
  failed: 'Muvaffaqiyatsiz',
}

export const cargoStatusColor: Record<CargoStatus, 'blue' | 'yellow' | 'green' | 'red' | 'gray'> = {
  new: 'blue',
  assigned: 'yellow',
  picked_up: 'yellow',
  in_transit: 'yellow',
  delivered: 'green',
  cancelled: 'gray',
  failed: 'red',
}

export const assignmentStatusLabel: Record<AssignmentStatus, string> = {
  proposed: 'Taklif qilindi',
  accepted: 'Qabul qilindi',
  rejected: 'Rad etildi',
  in_progress: 'Jarayonda',
  completed: 'Tugatildi',
  cancelled: 'Bekor qilindi',
}

export const bodyTypeLabel: Record<BodyType, string> = {
  tent: 'Tent',
  refrigerator: 'Refrijerator',
  flatbed: 'Ochiq',
  tank: 'Tsisterna',
  container: 'Konteyner',
  other: 'Boshqa',
}

export const companyKindLabel: Record<CompanyKind, string> = {
  carrier: 'Tashuvchi',
  shipper: 'Yuk egasi',
}
