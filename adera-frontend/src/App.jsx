import { lazy, Suspense } from 'react'
import { Routes, Route, Navigate } from 'react-router-dom'
import ProtectedRoute from './auth/ProtectedRoute'
import RouteEffects from './components/RouteEffects'
import Login from './pages/Login'
import Register from './pages/Register'
import UserPage from './pages/UserPage'
import ReportPage from './pages/ReportPage'
import ConfirmationPage from './pages/ConfirmationPage'
import AdminLayout from './components/admin/AdminLayout'
import AdminPage from './pages/AdminPage'
import AlertListPage from './pages/AlertListPage'
import InvestigationPage from './pages/InvestigationPage'
import EntityPage from './pages/EntityPage'
import EntitiesPage from './pages/EntitiesPage'
import CaseListPage from './pages/CaseListPage'
import CasePage from './pages/CasePage'

// The graph library is large, so this page loads only when someone opens it.
const GraphPage = lazy(() => import('./pages/GraphPage'))

export default function App() {
  return (
    <>
      <RouteEffects />
      <Routes>
        {/* open to everyone */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* any signed-in user */}
        <Route element={<ProtectedRoute />}>
          <Route path="/" element={<UserPage />} />
          <Route path="/report" element={<ReportPage />} />
          <Route path="/confirmation/:type" element={<ConfirmationPage />} />
        </Route>

        {/* analysts only: every page below sits inside the shared layout */}
        <Route element={<ProtectedRoute role="analyst" />}>
          <Route path="/admin" element={<AdminLayout />}>
            <Route index element={<AdminPage />} />
            <Route path="alerts" element={<AlertListPage />} />
            <Route path="alerts/:id" element={<InvestigationPage />} />
            <Route path="entities" element={<EntitiesPage />} />
            <Route path="entity/:phone" element={<EntityPage />} />
            <Route
              path="entity/:phone/graph"
              element={
                <Suspense fallback={<p className="op-empty">Loading graph…</p>}>
                  <GraphPage />
                </Suspense>
              }
            />
            <Route path="cases" element={<CaseListPage />} />
            <Route path="cases/:id" element={<CasePage />} />
          </Route>
        </Route>

        {/* anything else goes to the home page */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </>
  )
}
