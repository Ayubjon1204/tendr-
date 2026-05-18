import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { companiesApi } from '@/api/endpoints'
import {
  Badge,
  Card,
  CardContent,
  EmptyState,
  Input,
  Select,
  Spinner,
} from '@/components/ui'
import PageHeader from '@/components/PageHeader'
import { carrierTypeLabel, companyKindLabel } from '@/lib/formatters'
import type { CompanyKind } from '@/types/api'

export default function CompaniesPage() {
  const [kindFilter, setKindFilter] = useState<CompanyKind | ''>('')
  const [q, setQ] = useState('')

  const companies = useQuery({
    queryKey: ['companies', kindFilter, q],
    queryFn: () =>
      companiesApi.list({
        kind: kindFilter || undefined,
        q: q || undefined,
      }),
  })

  return (
    <div>
      <PageHeader
        title="Kompaniyalar"
        description="Tashuvchilar (carriers) va yuk egalari (shippers)"
      />

      <div className="p-8 space-y-4">
        <div className="flex items-center gap-3">
          <Select
            value={kindFilter}
            onChange={(e) => setKindFilter(e.target.value as CompanyKind | '')}
            className="w-56"
          >
            <option value="">Barcha turlari</option>
            <option value="factory">Zavodlar</option>
            <option value="carrier">Tashuvchilar</option>
            <option value="distributor">Distributorlar</option>
          </Select>
          <Input
            placeholder="Nom bo'yicha qidirish..."
            value={q}
            onChange={(e) => setQ(e.target.value)}
            className="max-w-sm"
          />
        </div>

        <Card>
          <CardContent className="p-0">
            {companies.isLoading ? (
              <div className="p-8 text-center"><Spinner /></div>
            ) : !companies.data || companies.data.length === 0 ? (
              <EmptyState title="Kompaniya topilmadi" />
            ) : (
              <table className="w-full text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500">
                  <tr>
                    <th className="text-left px-6 py-3 font-medium">Nom</th>
                    <th className="text-left px-6 py-3 font-medium">Turi</th>
                    <th className="text-left px-6 py-3 font-medium">Carrier subtype</th>
                    <th className="text-left px-6 py-3 font-medium">STIR</th>
                    <th className="text-left px-6 py-3 font-medium">Telefon</th>
                    <th className="text-left px-6 py-3 font-medium">Manzil</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {companies.data.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-50">
                      <td className="px-6 py-3 font-medium">{c.name}</td>
                      <td className="px-6 py-3">
                        <Badge variant={c.kind === 'carrier' ? 'blue' : c.kind === 'factory' ? 'yellow' : 'green'}>
                          {companyKindLabel[c.kind]}
                        </Badge>
                      </td>
                      <td className="px-6 py-3 text-slate-600 text-xs">
                        {c.carrier_type ? carrierTypeLabel[c.carrier_type] : '—'}
                      </td>
                      <td className="px-6 py-3 text-slate-600">{c.tax_id ?? '—'}</td>
                      <td className="px-6 py-3 text-slate-600">{c.phone ?? '—'}</td>
                      <td className="px-6 py-3 text-slate-600">{c.address ?? '—'}</td>
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
