import { useQuery } from '@tanstack/react-query'
import {
  Activity,
  AlertTriangle,
  ArrowRight,
  Clock,
  PackageOpen,
  Recycle,
  Truck,
  TrendingUp,
} from 'lucide-react'
import { Link } from 'react-router-dom'
import { dashboardApi } from '@/api/endpoints'
import {
  Badge,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  EmptyState,
  Spinner,
} from '@/components/ui'
import PageHeader from '@/components/PageHeader'
import { formatDistance, formatNumber, formatRelative } from '@/lib/formatters'

export default function DashboardPage() {
  const summary = useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: () => dashboardApi.summary(),
    refetchInterval: 30_000,
  })
  const idle = useQuery({
    queryKey: ['dashboard', 'idle-trucks'],
    queryFn: () => dashboardApi.idleTrucks(2),
    refetchInterval: 60_000,
  })
  const urgent = useQuery({
    queryKey: ['dashboard', 'urgent-cargo'],
    queryFn: () => dashboardApi.urgentCargo(24),
    refetchInterval: 60_000,
  })
  const backhaul = useQuery({
    queryKey: ['dashboard', 'back-haul'],
    queryFn: () => dashboardApi.backHaul(50),
    refetchInterval: 60_000,
  })

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="Tezkor ko'rsatkichlar va e'tibor talab qiluvchi masalalar"
      />

      <div className="p-8 space-y-6">
        {/* Top counters */}
        {summary.data ? (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
            <StatCard
              title="Fleet utilization"
              value={`${summary.data.fleet_utilization_pct}%`}
              detail={`${summary.data.busy_trucks} band / ${summary.data.total_trucks} jami`}
              icon={<TrendingUp className="size-5" />}
              accent="green"
            />
            <StatCard
              title="Bo'sh mashinalar"
              value={formatNumber(summary.data.available_trucks)}
              detail="Ish kutmoqda"
              icon={<Truck className="size-5" />}
              accent="blue"
            />
            <StatCard
              title="Yangi yuklar"
              value={formatNumber(summary.data.new_cargo)}
              detail={`Biriktirilmagan (${summary.data.pending_assignments} taklif)`}
              icon={<PackageOpen className="size-5" />}
              accent="yellow"
            />
            <StatCard
              title="Bugun yetkazildi"
              value={formatNumber(summary.data.delivered_today)}
              detail={`${summary.data.in_transit_cargo} hozir yo'lda`}
              icon={<Activity className="size-5" />}
              accent="brand"
            />
          </div>
        ) : (
          <div className="flex items-center gap-3 text-slate-500">
            <Spinner />
            Statistika yuklanmoqda...
          </div>
        )}

        {/* Action widgets */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <CardHeader className="flex items-center justify-between flex-row">
              <div className="flex items-center gap-2">
                <Clock className="size-4 text-amber-600" />
                <CardTitle>Bo'sh turgan mashinalar</CardTitle>
              </div>
              {idle.data && idle.data.length > 0 && (
                <Badge variant="yellow">{idle.data.length}</Badge>
              )}
            </CardHeader>
            <CardContent className="p-0">
              {idle.isLoading ? (
                <div className="px-6 py-8 text-center">
                  <Spinner />
                </div>
              ) : !idle.data || idle.data.length === 0 ? (
                <EmptyState
                  title="Hammasi yaxshi"
                  description="2 soatdan ortiq bo'sh turgan mashina yo'q"
                />
              ) : (
                <ul className="divide-y divide-slate-100">
                  {idle.data.slice(0, 6).map((t) => (
                    <li
                      key={t.truck_id}
                      className="px-6 py-3 flex items-center justify-between"
                    >
                      <div>
                        <p className="font-medium text-slate-900">{t.plate_number}</p>
                        <p className="text-xs text-slate-500">{t.carrier_name}</p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium text-amber-600">
                          {t.hours_idle.toFixed(1)} soat
                        </p>
                        <p className="text-xs text-slate-400">
                          {formatRelative(t.idle_since)}
                        </p>
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex items-center justify-between flex-row">
              <div className="flex items-center gap-2">
                <AlertTriangle className="size-4 text-red-600" />
                <CardTitle>Muddati yaqinlashayotgan yuklar</CardTitle>
              </div>
              {urgent.data && urgent.data.length > 0 && (
                <Badge variant="red">{urgent.data.length}</Badge>
              )}
            </CardHeader>
            <CardContent className="p-0">
              {urgent.isLoading ? (
                <div className="px-6 py-8 text-center">
                  <Spinner />
                </div>
              ) : !urgent.data || urgent.data.length === 0 ? (
                <EmptyState title="Kechikish yo'q" description="24 soat ichida muddat tugaydigan yuk yo'q" />
              ) : (
                <ul className="divide-y divide-slate-100">
                  {urgent.data.slice(0, 6).map((c) => (
                    <li
                      key={c.cargo_id}
                      className="px-6 py-3 flex items-center justify-between"
                    >
                      <div className="min-w-0">
                        <p className="font-medium text-slate-900 truncate">
                          {c.reference_code}
                        </p>
                        <p className="text-xs text-slate-500 truncate">
                          {c.origin_address} → {c.destination_address}
                        </p>
                      </div>
                      <div className="text-right shrink-0 ml-3">
                        <p
                          className={
                            'text-sm font-medium ' +
                            (c.hours_until_deadline < 6 ? 'text-red-600' : 'text-amber-600')
                          }
                        >
                          {c.hours_until_deadline.toFixed(1)} soat
                        </p>
                        {!c.has_assignment && (
                          <Badge variant="red" className="mt-0.5">Biriktirilmagan</Badge>
                        )}
                      </div>
                    </li>
                  ))}
                </ul>
              )}
            </CardContent>
          </Card>

          <Card className="lg:col-span-2">
            <CardHeader className="flex items-center justify-between flex-row">
              <div className="flex items-center gap-2">
                <Recycle className="size-4 text-emerald-600" />
                <CardTitle>Back-haul imkoniyatlari</CardTitle>
              </div>
              <p className="text-xs text-slate-500">
                Yetkazib boryotgan mashinalar yaqinida yangi yuklar
              </p>
            </CardHeader>
            <CardContent className="p-0">
              {backhaul.isLoading ? (
                <div className="px-6 py-8 text-center">
                  <Spinner />
                </div>
              ) : !backhaul.data || backhaul.data.length === 0 ? (
                <EmptyState
                  title="Hozir imkoniyat yo'q"
                  description="Mashinalar yetkazgach, yaqin yuklar bu yerda paydo bo'ladi"
                />
              ) : (
                <table className="w-full text-sm">
                  <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                    <tr>
                      <th className="text-left px-6 py-2 font-medium">Mashina</th>
                      <th className="text-left px-6 py-2 font-medium">Yetib boradi</th>
                      <th className="text-left px-6 py-2 font-medium">Yaqin yuk</th>
                      <th className="text-left px-6 py-2 font-medium">Masofa</th>
                      <th className="px-6 py-2"></th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {backhaul.data.slice(0, 8).map((o, idx) => (
                      <tr key={`${o.truck_id}-${o.nearby_cargo_id}-${idx}`}>
                        <td className="px-6 py-3 font-medium">{o.plate_number}</td>
                        <td className="px-6 py-3 text-slate-600">
                          {o.arriving_at_address}
                        </td>
                        <td className="px-6 py-3">
                          <div className="font-medium">{o.nearby_cargo_reference}</div>
                          <div className="text-xs text-slate-500">{o.nearby_cargo_origin}</div>
                        </td>
                        <td className="px-6 py-3 text-emerald-600 font-medium">
                          {formatDistance(o.distance_km)}
                        </td>
                        <td className="px-6 py-3 text-right">
                          <Link
                            to={`/cargo/${o.nearby_cargo_id}`}
                            className="inline-flex items-center text-brand-600 hover:text-brand-700 text-sm font-medium"
                          >
                            Ko'rish <ArrowRight className="size-4 ml-1" />
                          </Link>
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
    </div>
  )
}

function StatCard({
  title,
  value,
  detail,
  icon,
  accent,
}: {
  title: string
  value: string
  detail: string
  icon: React.ReactNode
  accent: 'green' | 'blue' | 'yellow' | 'brand'
}) {
  const accents = {
    green: 'bg-green-100 text-green-700',
    blue: 'bg-blue-100 text-blue-700',
    yellow: 'bg-yellow-100 text-yellow-700',
    brand: 'bg-brand-100 text-brand-700',
  }
  return (
    <Card>
      <CardContent>
        <div className="flex items-start justify-between">
          <div>
            <p className="text-sm text-slate-500">{title}</p>
            <p className="text-3xl font-bold text-slate-900 mt-1">{value}</p>
            <p className="text-xs text-slate-500 mt-1">{detail}</p>
          </div>
          <div className={'size-10 rounded-lg flex items-center justify-center ' + accents[accent]}>
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
