import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import Layout from '@/components/Layout'
import ProtectedRoute from '@/components/ProtectedRoute'
import LoginPage from '@/pages/LoginPage'
import DashboardPage from '@/pages/DashboardPage'
import CargoPage from '@/pages/CargoPage'
import NewCargoPage from '@/pages/NewCargoPage'
import TrucksPage from '@/pages/TrucksPage'
import DriversPage from '@/pages/DriversPage'
import CompaniesPage from '@/pages/CompaniesPage'
import PlaceholderPage from '@/pages/PlaceholderPage'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 10_000,
      retry: 1,
    },
  },
})

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<DashboardPage />} />
            <Route path="cargo" element={<CargoPage />} />
            <Route path="cargo/new" element={<NewCargoPage />} />
            <Route
              path="cargo/:id"
              element={<PlaceholderPage title="Yuk tafsilotlari" note="Sahifa keyingi bosqichda." />}
            />
            <Route path="trucks" element={<TrucksPage />} />
            <Route path="drivers" element={<DriversPage />} />
            <Route path="companies" element={<CompaniesPage />} />
            <Route
              path="map"
              element={
                <PlaceholderPage
                  title="Xarita"
                  note="Yandex Maps integratsiyasi Phase 5'da: mashinalar joylashuvi va marshrutlar."
                />
              }
            />
            <Route
              path="settings"
              element={
                <PlaceholderPage
                  title="Sozlamalar"
                  note="Tizim sozlamalari (foydalanuvchilar, role'lar, optimizatsiya koeffitsientlari) — keyingi bosqichda."
                />
              }
            />
          </Route>
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  )
}
