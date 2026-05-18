import { useQuery } from '@tanstack/react-query'
import { driversApi } from '@/api/endpoints'
import { Badge, Card, CardContent, EmptyState, Spinner } from '@/components/ui'
import PageHeader from '@/components/PageHeader'

export default function DriversPage() {
  const drivers = useQuery({ queryKey: ['drivers'], queryFn: () => driversApi.list() })

  return (
    <div>
      <PageHeader title="Haydovchilar" />
      <div className="p-8">
        <Card>
          <CardContent className="p-0">
            {drivers.isLoading ? (
              <div className="p-8 text-center"><Spinner /></div>
            ) : !drivers.data || drivers.data.length === 0 ? (
              <EmptyState title="Haydovchi topilmadi" />
            ) : (
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                  <tr>
                    <th className="text-left px-6 py-3 font-medium">F.I.O.</th>
                    <th className="text-left px-6 py-3 font-medium">Telefon</th>
                    <th className="text-left px-6 py-3 font-medium">Litsenziya</th>
                    <th className="text-left px-6 py-3 font-medium">Hozir mashinada</th>
                    <th className="text-left px-6 py-3 font-medium">Holat</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {drivers.data.map((d) => (
                    <tr key={d.id} className="hover:bg-slate-50">
                      <td className="px-6 py-3 font-medium">{d.full_name}</td>
                      <td className="px-6 py-3 text-slate-600">{d.phone}</td>
                      <td className="px-6 py-3 text-slate-600">{d.license_number ?? '—'}</td>
                      <td className="px-6 py-3 text-slate-600">{d.current_truck_id ? 'Ha' : '—'}</td>
                      <td className="px-6 py-3">
                        <Badge variant={d.is_active ? 'green' : 'gray'}>
                          {d.is_active ? 'Aktiv' : 'Nofaol'}
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
