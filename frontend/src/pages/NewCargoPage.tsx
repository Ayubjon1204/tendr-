import { type FormEvent, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation, useQuery } from '@tanstack/react-query'
import { cargoApi, companiesApi } from '@/api/endpoints'
import { extractError } from '@/api/client'
import {
  Button,
  Card,
  CardContent,
  Input,
  Label,
  Select,
  Spinner,
} from '@/components/ui'
import PageHeader from '@/components/PageHeader'
import { bodyTypeLabel } from '@/lib/formatters'
import type { BodyType } from '@/types/api'

const UZ_CITIES: Record<string, { lat: number; lng: number }> = {
  Toshkent: { lat: 41.2995, lng: 69.2401 },
  Samarqand: { lat: 39.6542, lng: 66.9597 },
  Buxoro: { lat: 39.7747, lng: 64.4286 },
  Andijon: { lat: 40.7821, lng: 72.3442 },
  Namangan: { lat: 40.9983, lng: 71.6726 },
  "Farg'ona": { lat: 40.3864, lng: 71.7864 },
  Qarshi: { lat: 38.8606, lng: 65.7886 },
  Termiz: { lat: 37.2242, lng: 67.2783 },
  Nukus: { lat: 42.4531, lng: 59.6103 },
  Urganch: { lat: 41.5503, lng: 60.6311 },
  Jizzax: { lat: 40.1158, lng: 67.8422 },
  Navoiy: { lat: 40.0844, lng: 65.3792 },
}

export default function NewCargoPage() {
  const navigate = useNavigate()
  const factories = useQuery({
    queryKey: ['companies', 'factories'],
    queryFn: () => companiesApi.list({ kind: 'factory' }),
  })
  const distributors = useQuery({
    queryKey: ['companies', 'distributors'],
    queryFn: () => companiesApi.list({ kind: 'distributor' }),
  })

  const [factoryId, setFactoryId] = useState('')
  const [distributorId, setDistributorId] = useState('')
  const [refCode, setRefCode] = useState('TND-' + Math.floor(Math.random() * 1_000_000))
  const [originCity, setOriginCity] = useState('Toshkent')
  const [destinationCity, setDestinationCity] = useState('Samarqand')
  const [weight, setWeight] = useState('5000')
  const [bodyType, setBodyType] = useState<BodyType | ''>('')
  const [pickupStart, setPickupStart] = useState(localISO(addHours(2)))
  const [pickupEnd, setPickupEnd] = useState(localISO(addHours(8)))
  const [deadline, setDeadline] = useState(localISO(addHours(36)))
  const [error, setError] = useState<string | null>(null)

  const createMutation = useMutation({
    mutationFn: () =>
      cargoApi.create({
        factory_id: factoryId,
        distributor_id: distributorId,
        reference_code: refCode,
        weight_kg: parseInt(weight, 10),
        required_body_type: bodyType || null,
        origin_address: `${originCity}, zavod ombori`,
        origin_location: UZ_CITIES[originCity],
        destination_address: `${destinationCity}, distributor`,
        destination_location: UZ_CITIES[destinationCity],
        pickup_window_start: new Date(pickupStart).toISOString(),
        pickup_window_end: new Date(pickupEnd).toISOString(),
        delivery_deadline: new Date(deadline).toISOString(),
      }),
    onSuccess: () => navigate('/cargo'),
    onError: (err) => setError(extractError(err)),
  })

  function onSubmit(e: FormEvent) {
    e.preventDefault()
    setError(null)
    if (!factoryId) {
      setError('Zavodni tanlang')
      return
    }
    if (!distributorId) {
      setError('Distributorni tanlang')
      return
    }
    createMutation.mutate()
  }

  const loading = factories.isLoading || distributors.isLoading

  return (
    <div>
      <PageHeader
        title="Yangi yuk"
        description="Zavoddan distributorgacha yuk. Tarqatish keyingi bosqichda."
      />

      <div className="p-8">
        <Card className="max-w-3xl">
          <CardContent>
            {loading ? (
              <Spinner />
            ) : (
              <form onSubmit={onSubmit} className="space-y-5">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label required>Zavod (yuboruvchi)</Label>
                    <Select value={factoryId} onChange={(e) => setFactoryId(e.target.value)} required>
                      <option value="">Tanlang...</option>
                      {factories.data?.map((s) => (
                        <option key={s.id} value={s.id}>{s.name}</option>
                      ))}
                    </Select>
                  </div>
                  <div className="space-y-1.5">
                    <Label required>Distributor (qabul qiluvchi)</Label>
                    <Select value={distributorId} onChange={(e) => setDistributorId(e.target.value)} required>
                      <option value="">Tanlang...</option>
                      {distributors.data?.map((s) => (
                        <option key={s.id} value={s.id}>{s.name}</option>
                      ))}
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label required>Reference code</Label>
                    <Input value={refCode} onChange={(e) => setRefCode(e.target.value)} required />
                  </div>
                  <div className="space-y-1.5">
                    <Label>Kuzov turi</Label>
                    <Select value={bodyType} onChange={(e) => setBodyType(e.target.value as BodyType | '')}>
                      <option value="">Farqi yo'q</option>
                      {Object.entries(bodyTypeLabel).map(([k, v]) => (
                        <option key={k} value={k}>{v}</option>
                      ))}
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <Label required>Yuklash shahri</Label>
                    <Select value={originCity} onChange={(e) => setOriginCity(e.target.value)}>
                      {Object.keys(UZ_CITIES).map((c) => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </Select>
                  </div>
                  <div className="space-y-1.5">
                    <Label required>Tushirish shahri</Label>
                    <Select value={destinationCity} onChange={(e) => setDestinationCity(e.target.value)}>
                      {Object.keys(UZ_CITIES).map((c) => (
                        <option key={c} value={c}>{c}</option>
                      ))}
                    </Select>
                  </div>
                </div>

                <div className="space-y-1.5">
                  <Label required>Og'irlik (kg)</Label>
                  <Input
                    type="number"
                    min={1}
                    value={weight}
                    onChange={(e) => setWeight(e.target.value)}
                    required
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="space-y-1.5">
                    <Label required>Yuklash boshlanishi</Label>
                    <Input
                      type="datetime-local"
                      value={pickupStart}
                      onChange={(e) => setPickupStart(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label required>Yuklash tugashi</Label>
                    <Input
                      type="datetime-local"
                      value={pickupEnd}
                      onChange={(e) => setPickupEnd(e.target.value)}
                      required
                    />
                  </div>
                  <div className="space-y-1.5">
                    <Label required>Yetkazib berish deadline</Label>
                    <Input
                      type="datetime-local"
                      value={deadline}
                      onChange={(e) => setDeadline(e.target.value)}
                      required
                    />
                  </div>
                </div>

                {error && (
                  <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
                    {error}
                  </div>
                )}

                <div className="flex items-center gap-3 pt-2">
                  <Button type="submit" disabled={createMutation.isPending}>
                    {createMutation.isPending ? 'Saqlanmoqda...' : 'Saqlash'}
                  </Button>
                  <Button type="button" variant="ghost" onClick={() => navigate(-1)}>
                    Bekor qilish
                  </Button>
                </div>
              </form>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function addHours(h: number): Date {
  return new Date(Date.now() + h * 3600 * 1000)
}

function localISO(d: Date): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}
