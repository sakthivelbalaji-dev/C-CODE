import { Navigate, Route, Routes } from 'react-router-dom'
import DashboardPage from './pages/DashboardPage'
import LoginPage from './pages/LoginPage'
import QuestionPage from './pages/QuestionPage'
import ResultPage from './pages/ResultPage'
import AdminPage from './pages/AdminPage'
import ProfilePage from './pages/ProfilePage'
import SyllabusPage from './pages/SyllabusPage'
import LeaderboardPage from './pages/LeaderboardPage'

function getCurrentUser() {
  try {
    const raw = localStorage.getItem('ccodelab_user')
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

function ProtectedRoute({ children, allowedRoles }) {
  const user = getCurrentUser()
  if (!user) return <Navigate to="/login" replace />
  if (allowedRoles && !allowedRoles.includes(user.role)) {
    return <Navigate to={user.role === 'staff' ? '/admin' : '/dashboard'} replace />
  }
  return children
}

function PublicOnlyRoute({ children }) {
  const user = getCurrentUser()
  if (!user) return children
  return <Navigate to={user.role === 'staff' ? '/admin' : '/dashboard'} replace />
}

function App() {
  return (
    <Routes>
      <Route path="/" element={<Navigate to="/login" replace />} />
      <Route
        path="/login"
        element={
          <PublicOnlyRoute>
            <LoginPage />
          </PublicOnlyRoute>
        }
      />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute allowedRoles={['student']}>
            <DashboardPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/question"
        element={
          <ProtectedRoute allowedRoles={['student']}>
            <QuestionPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/result"
        element={
          <ProtectedRoute allowedRoles={['student']}>
            <ResultPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin"
        element={
          <ProtectedRoute allowedRoles={['staff']}>
            <AdminPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/profile"
        element={
          <ProtectedRoute allowedRoles={['student']}>
            <ProfilePage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/syllabus"
        element={
          <ProtectedRoute allowedRoles={['student']}>
            <SyllabusPage />
          </ProtectedRoute>
        }
      />
      <Route
        path="/leaderboard"
        element={
          <ProtectedRoute allowedRoles={['student', 'staff']}>
            <LeaderboardPage />
          </ProtectedRoute>
        }
      />
    </Routes>
  )
}

export default App
