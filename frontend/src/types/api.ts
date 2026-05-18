// Backend Pydantic schema'lariga mos TypeScript turlari (Phase 2 multi-tenant).

export type UUID = string
export type ISODateTime = string

export interface GeoPoint {
  lat: number
  lng: number
}

export type UserRole = 'owner' | 'admin' | 'dispatcher' | 'accountant' | 'viewer'

export interface User {
  id: UUID
  email: string
  full_name: string
  role: UserRole
  company_id: UUID | null
  is_active: boolean
  created_at: ISODateTime
}

export interface TokenResponse {
  access_token: string
  token_type: string
  expires_in: number
}

export type CompanyKind = 'factory' | 'carrier' | 'distributor'
export type CarrierType = 'hybrid' | 'forwarder' | 'asset_only'

export interface Company {
  id: UUID
  name: string
  kind: CompanyKind
  carrier_type: CarrierType | null
  tax_id?: string | null
  phone?: string | null
  email?: string | null
  address?: string | null
  is_active: boolean
  created_at: ISODateTime
  updated_at: ISODateTime
}

export type BodyType = 'tent' | 'refrigerator' | 'flatbed' | 'tank' | 'container' | 'other'

export type TruckStatus =
  | 'available'
  | 'busy'
  | 'loading'
  | 'unloading'
  | 'maintenance'
  | 'off_duty'

export type SpotSource = 'lorry' | 'telegram' | 'manual'

export interface Truck {
  id: UUID
  carrier_id: UUID | null
  is_spot: boolean
  spot_source: SpotSource | null
  plate_number: string
  model?: string | null
  capacity_kg: number
  capacity_volume_m3?: number | string | null
  body_type: BodyType
  status: TruckStatus
  current_location?: GeoPoint | null
  home_base_location?: GeoPoint | null
  last_location_update?: ISODateTime | null
  is_active: boolean
  created_at: ISODateTime
  updated_at: ISODateTime
}

export interface Driver {
  id: UUID
  carrier_id: UUID
  full_name: string
  phone: string
  license_number?: string | null
  current_truck_id?: UUID | null
  is_active: boolean
  created_at: ISODateTime
  updated_at: ISODateTime
}

export type CargoStatus =
  | 'new'
  | 'distributed'
  | 'carrier_accepted'
  | 'assigned_truck'
  | 'picked_up'
  | 'in_transit'
  | 'delivered'
  | 'completed'
  | 'cancelled'
  | 'failed'

export interface Cargo {
  id: UUID
  factory_id: UUID
  distributor_id: UUID
  reference_code: string
  description?: string | null
  weight_kg: number
  volume_m3?: number | string | null
  required_body_type?: BodyType | null
  origin_address: string
  origin_location: GeoPoint
  destination_address: string
  destination_location: GeoPoint
  pickup_window_start: ISODateTime
  pickup_window_end: ISODateTime
  delivery_deadline: ISODateTime
  price?: number | string | null
  status: CargoStatus
  created_at: ISODateTime
  updated_at: ISODateTime
}

export type AssignmentStatus =
  | 'proposed'
  | 'accepted'
  | 'forwarded'
  | 'rejected'
  | 'in_progress'
  | 'completed'
  | 'cancelled'

export type AssignmentSource = 'system' | 'factory' | 'carrier'

export interface Assignment {
  id: UUID
  cargo_id: UUID
  carrier_id: UUID
  parent_assignment_id: UUID | null
  truck_id?: UUID | null
  driver_id?: UUID | null
  status: AssignmentStatus
  assigned_by: AssignmentSource
  planned_pickup_at: ISODateTime
  planned_delivery_at: ISODateTime
  actual_pickup_at?: ISODateTime | null
  actual_delivery_at?: ISODateTime | null
  price?: number | string | null
  optimization_score?: number | string | null
  notes?: string | null
  created_at: ISODateTime
  updated_at: ISODateTime
}

export type DocumentKind =
  | 'ttn'
  | 'delivery_receipt'
  | 'discrepancy_act'
  | 'invoice'
  | 'contract'

export type DocumentStatus =
  | 'created'
  | 'issued'
  | 'picked_up_signed'
  | 'delivered_signed'
  | 'discrepancy'
  | 'cancelled'

export interface Document {
  id: UUID
  cargo_id: UUID
  kind: DocumentKind
  status: DocumentStatus
  number: string | null
  factory_signed_at?: ISODateTime | null
  driver_pickup_signed_at?: ISODateTime | null
  driver_delivery_signed_at?: ISODateTime | null
  distributor_signed_at?: ISODateTime | null
  discrepancy_notes?: string | null
  actual_weight_kg?: number | null
  actual_volume_m3?: number | string | null
  pdf_url?: string | null
  qr_code_payload?: string | null
  created_at: ISODateTime
  updated_at: ISODateTime
}

export interface TruckCandidate {
  truck_id: UUID
  plate_number: string
  score: number
  distance_to_pickup_km: number
  capacity_kg: number
  body_type: BodyType
  reasons: string[]
}

export interface AutoAssignResult {
  cargo_id: UUID
  chosen?: TruckCandidate | null
  candidates: TruckCandidate[]
  assignment_id?: UUID | null
  message: string
}

export interface DashboardSummary {
  total_trucks: number
  available_trucks: number
  busy_trucks: number
  off_duty_trucks: number
  new_cargo: number
  assigned_cargo: number
  in_transit_cargo: number
  delivered_today: number
  pending_assignments: number
  active_carriers: number
  active_factories: number
  active_distributors: number
  fleet_utilization_pct: number
}

export interface IdleTruck {
  truck_id: UUID
  plate_number: string
  carrier_name: string
  idle_since?: ISODateTime | null
  last_location_address?: string | null
  hours_idle: number
}

export interface UrgentCargo {
  cargo_id: UUID
  reference_code: string
  origin_address: string
  destination_address: string
  weight_kg: number
  delivery_deadline: ISODateTime
  hours_until_deadline: number
  has_assignment: boolean
}

export interface BackHaulOpportunity {
  truck_id: UUID
  plate_number: string
  arriving_at_address: string
  arriving_at: ISODateTime
  nearby_cargo_id: UUID
  nearby_cargo_reference: string
  nearby_cargo_origin: string
  distance_km: number
}
