import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { companiesApi, trucksApi } from '@/api/endpoints'
import {
  Badge,
  Card,
  CardContent,
  EmptyState,
  Select,
  Spinner,
} from '@/components/ui'
import PageHeader from '@/components/PageHeader'
import {
  bodyTypeLabel,
  formatRelative,
  formatWeight,
  truckStatusColor,
  truckStatusLabel,
} from '@/lib/formatters'
import type { TruckStatus } from '@/types/api'

export default function TrucksPage() {
  const [statusFilter, setStatusFilter] = useState<TruckStatus | ''>('')
  const [carrierId, setCarrierId] = useState('')

  const carriers = useQuery({
    queryKey: ['companies', 'carriers'],
    queryFn: () => companiesApi.list({ kind: 'carrier' }),
  })
  const trucks = useQuery({
    queryKey: ['trucks', statusFilter || 'all', carrierId || 'all'],
    queryFn: () =>
      trucksApi.list({
        status: statusFilter || undefined,
        carrier_id: carrierId || undefined,
      }),
  })

  return (
    <div>
      <PageHeader
        title="Mashinalar"
        description="Transport kompaniyalari mashinalari"
      />

      <div className="p-8 space-y-4">
        <div className="flex items-center gap-3">
          <Select
            value={carrierId}
            onChange={(e) => setCarrierId(e.target.value)}
            className="w-64"
          >
            <option value="">Barcha kompaniyalar</option>
            {carriers.data?.map((c) => (
              <option key={c.id} value={c.id}>{c.name}</option>
            ))}
          </Select>
          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as TruckStatus | '')}
            className="w-48"
          >
            <option value="">Barcha holatlar</option>
            {Object.entries(truckStatusLabel).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </Select>
        </div>

        <Card>
          <CardContent className="p-0">
            {trucks.isLoading ? (
              <div className="p-8 text-center"><Spinner /></div>
            ) : !trucks.data || trucks.data.length === 0 ? (
              <EmptyState title="Mashina topilmadi" />
            ) : (
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                  <tr>
                    <th className="text-left px-6 py-3 font-medium">Raqam</th>
                    <th className="text-left px-6 py-3 font-medium">Model</th>
                    <th className="text-left px-6 py-3 font-medium">Sig'im</th>
                    <th className="text-left px-6 py-3 font-medium">Kuzov</th>
                    <th className="text-left px-6 py-3 font-medium">Status</th>
                    <th className="text-left px-6 py-3 font-medium">So'ngi yangilanish</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {trucks.data.map((t) => (
                    <tr key={t.id} className="hover:bg-slate-50">
                      <td className="px-6 py-3 font-medium">{t.plate_number}</td>
                      <td className="px-6 py-3 text-slate-700">{t.model ?? '—'}</td>
                      <td className="px-6 py-3 text-slate-700">{formatWeight(t.capacity_kg)}</td>
                      <td className="px-6 py-3 text-slate-700">{bodyTypeLabel[t.body_type]}</td>
                      <td className="px-6 py-3">
                        <Badge variant={truckStatusColor[t.status]}>{truckStatusLabel[t.status]}</Badge>
                      </td>
                      <td className="px-6 py-3 text-slate-500 text-xs">
                        {formatRelative(t.last_location_update)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
