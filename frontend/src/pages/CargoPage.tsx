import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Plus } from 'lucide-react'
import { cargoApi } from '@/api/endpoints'
import {
  Badge,
  Button,
  Card,
  CardContent,
  EmptyState,
  Select,
  Spinner,
} from '@/components/ui'
import PageHeader from '@/components/PageHeader'
import {
  cargoStatusColor,
  cargoStatusLabel,
  formatDateTime,
  formatWeight,
} from '@/lib/formatters'
import type { CargoStatus } from '@/types/api'

export default function CargoPage() {
  const [statusFilter, setStatusFilter] = useState<CargoStatus | ''>('')
  const cargo = useQuery({
    queryKey: ['cargo', statusFilter || 'all'],
    queryFn: () => cargoApi.list(statusFilter ? { status: statusFilter } : undefined),
  })

  return (
    <div>
      <PageHeader
        title="Yuklar"
        description="Mavjud yuklar ro'yxati va statuslari"
        actions={
          <Link to="/cargo/new">
            <Button>
              <Plus className="size-4 mr-1" /> Yangi yuk
            </Button>
          </Link>
        }
      />

      <div className="p-8 space-y-4">
        <div className="flex items-center gap-3">
          <Select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value as CargoStatus | '')}
            className="w-56"
          >
            <option value="">Barcha statuslar</option>
            {Object.entries(cargoStatusLabel).map(([k, v]) => (
              <option key={k} value={k}>{v}</option>
            ))}
          </Select>
        </div>

        <Card>
          <CardContent className="p-0">
            {cargo.isLoading ? (
              <div className="p-8 text-center">
                <Spinner />
              </div>
            ) : !cargo.data || cargo.data.length === 0 ? (
              <EmptyState title="Yuklar topilmadi" description="Yangi yuk qo'shing yoki filterni o'zgartiring" />
            ) : (
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                  <tr>
                    <th className="text-left px-6 py-3 font-medium">Raqam</th>
                    <th className="text-left px-6 py-3 font-medium">Yo'nalish</th>
                    <th className="text-left px-6 py-3 font-medium">Og'irlik</th>
                    <th className="text-left px-6 py-3 font-medium">Olish vaqti</th>
                    <th className="text-left px-6 py-3 font-medium">Deadline</th>
                    <th className="text-left px-6 py-3 font-medium">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {cargo.data.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-50">
                      <td className="px-6 py-3 font-medium">
                        <Link to={`/cargo/${c.id}`} className="text-brand-600 hover:text-brand-700">
                          {c.reference_code}
                        </Link>
                      </td>
                      <td className="px-6 py-3 text-slate-700">
                        <div>{c.origin_address}</div>
                        <div className="text-slate-400 text-xs">→ {c.destination_address}</div>
                      </td>
                      <td className="px-6 py-3 text-slate-700">{formatWeight(c.weight_kg)}</td>
                      <td className="px-6 py-3 text-slate-600 text-xs">
                        {formatDateTime(c.pickup_window_start)}
                      </td>
                      <td className="px-6 py-3 text-slate-600 text-xs">
                        {formatDateTime(c.delivery_deadline)}
                      </td>
                      <td className="px-6 py-3">
                        <Badge variant={cargoStatusColor[c.status]}>
                          {cargoStatusLabel[c.status]}
                        </Badge>
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
