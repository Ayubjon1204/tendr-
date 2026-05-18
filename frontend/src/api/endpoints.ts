import { api } from './client'
import type {
  Assignment,
  AutoAssignResult,
  BackHaulOpportunity,
  Cargo,
  Company,
  CompanyKind,
  DashboardSummary,
  Driver,
  IdleTruck,
  TokenResponse,
  Truck,
  TruckStatus,
  UrgentCargo,
  User,
} from '@/types/api'

// ---------- Auth ----------
export const authApi = {
  async login(email: string, password: string): Promise<TokenResponse> {
    const form = new URLSearchParams()
    form.append('username', email)
    form.append('password', password)
    const { data } = await api.post<TokenResponse>('/auth/login', form, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    return data
  },
  async me(): Promise<User> {
    const { data } = await api.get<User>('/auth/me')
    return data
  },
}

// ---------- Companies ----------
export const companiesApi = {
  async list(params?: { kind?: CompanyKind; q?: string }): Promise<Company[]> {
    const { data } = await api.get<Company[]>('/companies', { params })
    return data
  },
  async get(id: string): Promise<Company> {
    const { data } = await api.get<Company>(`/companies/${id}`)
    return data
  },
  async create(payload: Partial<Company>): Promise<Company> {
    const { data } = await api.post<Company>('/companies', payload)
    return data
  },
  async update(id: string, payload: Partial<Company>): Promise<Company> {
    const { data } = await api.patch<Company>(`/companies/${id}`, payload)
    return data
  },
}

// ---------- Trucks ----------
export const trucksApi = {
  async list(params?: {
    carrier_id?: string
    status?: TruckStatus
    is_active?: boolean
  }): Promise<Truck[]> {
    const { data } = await api.get<Truck[]>('/trucks', { params })
    return data
  },
  async get(id: string): Promise<Truck> {
    const { data } = await api.get<Truck>(`/trucks/${id}`)
    return data
  },
  async create(payload: Partial<Truck> & { carrier_id: string }): Promise<Truck> {
    const { data } = await api.post<Truck>('/trucks', payload)
    return data
  },
}

// ---------- Drivers ----------
export const driversApi = {
  async list(params?: { carrier_id?: string }): Promise<Driver[]> {
    const { data } = await api.get<Driver[]>('/drivers', { params })
    return data
  },
}

// ---------- Cargo ----------
export const cargoApi = {
  async list(params?: { status?: string }): Promise<Cargo[]> {
    const { data } = await api.get<Cargo[]>('/cargo', { params })
    return data
  },
  async get(id: string): Promise<Cargo> {
    const { data } = await api.get<Cargo>(`/cargo/${id}`)
    return data
  },
  async create(payload: Record<string, unknown>, autoAssign = true): Promise<Cargo> {
    const { data } = await api.post<Cargo>('/cargo', payload, {
      params: { auto_assign: autoAssign },
    })
    return data
  },
}

// ---------- Assignments ----------
export const assignmentsApi = {
  async list(params?: { status?: string; truck_id?: string }): Promise<Assignment[]> {
    const { data } = await api.get<Assignment[]>('/assignments', { params })
    return data
  },
  async autoAssign(cargoId: string): Promise<AutoAssignResult> {
    const { data } = await api.post<AutoAssignResult>('/assignments/auto', {
      cargo_id: cargoId,
    })
    return data
  },
  async previewAutoAssign(cargoId: string): Promise<AutoAssignResult> {
    const { data } = await api.post<AutoAssignResult>('/assignments/auto/preview', {
      cargo_id: cargoId,
    })
    return data
  },
}

// ---------- Dashboard ----------
export const dashboardApi = {
  async summary(): Promise<DashboardSummary> {
    const { data } = await api.get<DashboardSummary>('/dashboard/summary')
    return data
  },
  async idleTrucks(hours = 2): Promise<IdleTruck[]> {
    const { data } = await api.get<IdleTruck[]>('/dashboard/idle-trucks', {
      params: { hours_threshold: hours },
    })
    return data
  },
  async urgentCargo(hours = 24): Promise<UrgentCargo[]> {
    const { data } = await api.get<UrgentCargo[]>('/dashboard/urgent-cargo', {
      params: { hours_window: hours },
    })
    return data
  },
  async backHaul(radius = 50): Promise<BackHaulOpportunity[]> {
    const { data } = await api.get<BackHaulOpportunity[]>('/dashboard/back-haul', {
      params: { radius_km: radius },
    })
    return data
  },
}
