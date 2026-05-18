import { type FormEvent, useState } from 'react'
import { useNavigate, Navigate } from 'react-router-dom'
import { Truck } from 'lucide-react'
import { authApi } from '@/api/endpoints'
import { extractError } from '@/api/client'
import { useAuthStore } from '@/stores/authStore'
import { Button, Card, CardContent, Input, Label } from '@/components/ui'

export default function LoginPage() {
  const navigate = useNavigate()
  const { token, setToken } = useAuthStore()
  const [email, setEmail] = useState('admin@tendr.local')
  const [password, setPassword] = useState('admin123')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (token) return <Navigate to="/" replace />

  async function onSubmit(e: FormEvent) {
    e.preventDefault()
    setLoading(true)
    setError(null)
    try {
      const { access_token } = await authApi.login(email, password)
      setToken(access_token)
      navigate('/', { replace: true })
    } catch (err) {
      setError(extractError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <Card className="w-full max-w-md">
        <CardContent className="py-8">
          <div className="flex flex-col items-center mb-6">
            <div className="size-12 rounded-xl bg-brand-600 flex items-center justify-center mb-3">
              <Truck className="size-7 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900">Tendr</h1>
            <p className="text-sm text-slate-500 mt-1">Transport Management System</p>
          </div>

          <form onSubmit={onSubmit} className="space-y-4">
            <div className="space-y-1.5">
              <Label htmlFor="email" required>Email</Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="admin@tendr.local"
                required
                autoComplete="email"
              />
            </div>
            <div className="space-y-1.5">
              <Label htmlFor="password" required>Parol</Label>
              <Input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>

            {error && (
              <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded px-3 py-2">
                {error}
              </div>
            )}

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Kirilmoqda...' : 'Kirish'}
            </Button>

            <p className="text-xs text-slate-400 text-center mt-2">
              Demo: <code>admin@tendr.local</code> / <code>admin123</code>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
