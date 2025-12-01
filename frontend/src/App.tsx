import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AuthProvider } from './contexts/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Unauthorized from './pages/Unauthorized';
import PatientSearch from './pages/patients/PatientSearch';
import PatientForm from './pages/patients/PatientForm';
import PatientProfile from './pages/patients/PatientProfile';
import SessionCreate from './pages/sessions/SessionCreate';
import DoctorQueue from './pages/doctor/DoctorQueue';
import SessionReview from './pages/doctor/SessionReview';
import UserManagement from './pages/admin/UserManagement';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AuthProvider>
          <Router>
            <Routes>
              <Route path="/login" element={<Login />} />
              <Route path="/unauthorized" element={<Unauthorized />} />
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <Layout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<Dashboard />} />
                {/* Patient routes */}
                <Route path="patients" element={<PatientSearch />} />
                <Route path="patients/new" element={<PatientForm />} />
                <Route path="patients/:patientId" element={<PatientProfile />} />
                {/* Session routes */}
                <Route path="sessions/new" element={<SessionCreate />} />
                {/* Doctor routes */}
                <Route
                  path="doctor/queue"
                  element={
                    <ProtectedRoute allowedRoles={['doctor', 'admin']}>
                      <DoctorQueue />
                    </ProtectedRoute>
                  }
                />
                <Route
                  path="doctor/sessions/:sessionId"
                  element={
                    <ProtectedRoute allowedRoles={['doctor', 'admin']}>
                      <SessionReview />
                    </ProtectedRoute>
                  }
                />
                {/* Admin routes */}
                <Route
                  path="admin/users"
                  element={
                    <ProtectedRoute allowedRoles={['admin']}>
                      <UserManagement />
                    </ProtectedRoute>
                  }
                />
              </Route>
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Router>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;
