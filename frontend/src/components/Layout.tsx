import { NavLink, Outlet, useNavigate } from 'react-router-dom'
import {
  LayoutDashboard,
  Package,
  Truck,
  Building2,
  Users,
  Map,
  LogOut,
  Settings,
} from 'lucide-react'
import { useAuthStore } from '@/stores/authStore'
import { cn } from '@/lib/cn'

const nav = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard, end: true },
  { to: '/cargo', label: 'Yuklar', icon: Package },
  { to: '/trucks', label: 'Mashinalar', icon: Truck },
  { to: '/drivers', label: 'Haydovchilar', icon: Users },
  { to: '/companies', label: 'Kompaniyalar', icon: Building2 },
  { to: '/map', label: 'Xarita', icon: Map },
  { to: '/settings', label: 'Sozlamalar', icon: Settings },
]

export default function Layout() {
  const navigate = useNavigate()
  const logout = useAuthStore((s) => s.logout)

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="flex h-screen overflow-hidden bg-slate-50">
      <aside className="w-60 bg-white border-r border-slate-200 flex flex-col">
        <div className="px-6 py-5 border-b border-slate-200">
          <div className="flex items-center gap-2">
            <div className="size-9 rounded-lg bg-brand-600 flex items-center justify-center">
              <Truck className="size-5 text-white" />
            </div>
            <div>
              <h1 className="font-bold text-slate-900 leading-tight">Tendr</h1>
              <p className="text-xs text-slate-500">TMS</p>
            </div>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-0.5 overflow-y-auto">
          {nav.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                cn(
                  'flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors',
                  isActive
                    ? 'bg-brand-50 text-brand-700'
                    : 'text-slate-600 hover:bg-slate-100 hover:text-slate-900',
                )
              }
            >
              <Icon className="size-4" />
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-slate-200 p-3">
          <button
            onClick={handleLogout}
            className="flex items-center gap-3 w-full rounded-md px-3 py-2 text-sm font-medium text-slate-600 hover:bg-slate-100 hover:text-slate-900"
          >
            <LogOut className="size-4" />
            Chiqish
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  )
}
