import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { 
  Users, 
  MessageSquare, 
  AlertTriangle, 
  CheckCircle,
  ArrowRight,
  Activity
} from 'lucide-react'
import { dashboardApi } from '../api/client'
import clsx from 'clsx'

interface StatCardProps {
  title: string
  value: number
  icon: React.ComponentType<{ className?: string }>
  color: 'primary' | 'success' | 'warning' | 'danger'
}

function StatCard({ title, value, icon: Icon, color }: StatCardProps) {
  const colors = {
    primary: 'from-primary-500 to-primary-700 shadow-primary-600/30',
    success: 'from-success-500 to-success-700 shadow-success-600/30',
    warning: 'from-yellow-500 to-orange-600 shadow-yellow-600/30',
    danger: 'from-emergency-500 to-emergency-700 shadow-emergency-600/30',
  }

  return (
    <div className="card hover:border-[var(--color-border-hover)] transition-colors">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-sm font-medium" style={{ color: 'var(--color-text-secondary)' }}>{title}</p>
          <p className="text-3xl font-bold mt-2" style={{ color: 'var(--color-text-primary)' }}>{value}</p>
        </div>
        <div className={clsx(
          "w-12 h-12 rounded-xl bg-gradient-to-br flex items-center justify-center shadow-lg",
          colors[color]
        )}>
          <Icon className="w-6 h-6 text-white" />
        </div>
      </div>
    </div>
  )
}

export default function DashboardPage() {
  const { data: summaryData } = useQuery({
    queryKey: ['dashboard-summary'],
    queryFn: dashboardApi.getSummary,
  })

  const { data: patientsData, isLoading: patientsLoading } = useQuery({
    queryKey: ['dashboard-patients'],
    queryFn: () => dashboardApi.getPatients({ limit: 5 }),
  })

  const stats = summaryData?.data || {
    total_patients: 0,
    active_threads: 0,
    emergencies_today: 0,
    completed_today: 0,
  }

  const patients = patientsData?.data || []

  const getStatusBadge = (status: string | null) => {
    if (!status) return null
    
    const styles: Record<string, string> = {
      INTERVIEWING: 'bg-primary-500/20 text-primary-600 dark:text-primary-300 border border-primary-500/30',
      EMERGENCY: 'bg-emergency-500/20 text-emergency-600 dark:text-emergency-300 border border-emergency-500/30',
      CODING: 'bg-yellow-500/20 text-yellow-600 dark:text-yellow-300 border border-yellow-500/30',
      SCRIBING: 'bg-purple-500/20 text-purple-600 dark:text-purple-300 border border-purple-500/30',
      DONE: 'bg-success-500/20 text-success-600 dark:text-success-300 border border-success-500/30',
    }

    return (
      <span className={clsx('status-badge', styles[status] || styles.INTERVIEWING)}>
        {status}
      </span>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Stats grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Total Patients"
          value={stats.total_patients}
          icon={Users}
          color="primary"
        />
        <StatCard
          title="Active Triage"
          value={stats.active_threads}
          icon={MessageSquare}
          color="warning"
        />
        <StatCard
          title="Emergencies Today"
          value={stats.emergencies_today}
          icon={AlertTriangle}
          color="danger"
        />
        <StatCard
          title="Completed Today"
          value={stats.completed_today}
          icon={CheckCircle}
          color="success"
        />
      </div>

      {/* Recent patients */}
      <div className="card">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-lg font-semibold" style={{ color: 'var(--color-text-primary)' }}>Recent Patients</h2>
          <Link
            to="/patients"
            className="text-sm text-primary-500 hover:text-primary-400 flex items-center gap-1"
          >
            View all
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {patientsLoading ? (
          <div className="flex items-center justify-center py-8">
            <Activity className="w-6 h-6 text-primary-500 animate-spin" />
          </div>
        ) : patients.length === 0 ? (
          <div className="text-center py-8">
            <Users className="w-12 h-12 mx-auto mb-3" style={{ color: 'var(--color-text-muted)' }} />
            <p style={{ color: 'var(--color-text-secondary)' }}>No patients yet</p>
            <Link to="/patients" className="btn-primary inline-block mt-4">
              Add Patient
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr style={{ borderBottom: '1px solid var(--color-border)' }}>
                  <th className="text-left py-3 px-4 text-sm font-medium" style={{ color: 'var(--color-text-secondary)' }}>Name</th>
                  <th className="text-left py-3 px-4 text-sm font-medium" style={{ color: 'var(--color-text-secondary)' }}>Last Status</th>
                  <th className="text-left py-3 px-4 text-sm font-medium" style={{ color: 'var(--color-text-secondary)' }}>Active Threads</th>
                  <th className="text-right py-3 px-4 text-sm font-medium" style={{ color: 'var(--color-text-secondary)' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {patients.map((patient: any) => (
                  <tr 
                    key={patient.id} 
                    className="hover:bg-[var(--color-bg-hover)] transition-colors"
                    style={{ borderBottom: '1px solid var(--color-border)' }}
                  >
                    <td className="py-4 px-4">
                      <Link 
                        to={`/patients/${patient.id}`} 
                        className="font-medium hover:text-primary-500"
                        style={{ color: 'var(--color-text-primary)' }}
                      >
                        {patient.first_name} {patient.last_name}
                      </Link>
                    </td>
                    <td className="py-4 px-4">
                      {getStatusBadge(patient.last_triage_status)}
                    </td>
                    <td className="py-4 px-4" style={{ color: 'var(--color-text-secondary)' }}>
                      {patient.active_threads_count}
                    </td>
                    <td className="py-4 px-4 text-right">
                      <Link
                        to={`/patients/${patient.id}`}
                        className="text-sm text-primary-500 hover:text-primary-400"
                      >
                        View
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
