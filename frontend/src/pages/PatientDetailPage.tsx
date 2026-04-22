import { useState } from 'react'
import { useParams, useNavigate, Link } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  ArrowLeft, 
  MessageSquare, 
  Plus, 
  Activity,
  Calendar,
  Phone,
  Mail,
  AlertTriangle
} from 'lucide-react'
import { patientsApi, triageApi } from '../api/client'
import { format } from 'date-fns'
import clsx from 'clsx'

export default function PatientDetailPage() {
  const { patientId } = useParams<{ patientId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [showNewTriage, setShowNewTriage] = useState(false)
  const [chiefComplaint, setChiefComplaint] = useState('')

  const { data: patientData, isLoading: patientLoading } = useQuery({
    queryKey: ['patient', patientId],
    queryFn: () => patientsApi.get(patientId!),
    enabled: !!patientId,
  })

  const { data: threadsData, isLoading: threadsLoading } = useQuery({
    queryKey: ['threads', patientId],
    queryFn: () => triageApi.listThreads({ patient_id: patientId }),
    enabled: !!patientId,
  })

  const createThreadMutation = useMutation({
    mutationFn: () => triageApi.createThread(patientId!, chiefComplaint || undefined),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['threads', patientId] })
      navigate(`/triage/${data.data.id}`)
    },
  })

  const patient = patientData?.data
  const threads = threadsData?.data || []

  const getStatusBadge = (status: string) => {
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

  if (patientLoading) {
    return (
      <div className="flex items-center justify-center py-16">
        <Activity className="w-8 h-8 text-primary-500 animate-spin" />
      </div>
    )
  }

  if (!patient) {
    return (
      <div className="text-center py-16">
        <p style={{ color: 'var(--color-text-secondary)' }}>Patient not found</p>
        <Link to="/patients" className="btn-primary inline-block mt-4">
          Back to Patients
        </Link>
      </div>
    )
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/patients')}
          className="p-2 rounded-lg hover:bg-[var(--color-bg-hover)]"
          style={{ color: 'var(--color-text-secondary)' }}
        >
          <ArrowLeft className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-2xl font-bold" style={{ color: 'var(--color-text-primary)' }}>
            {patient.first_name} {patient.last_name}
          </h1>
        </div>
      </div>

      {/* Patient info */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Info card */}
        <div className="card">
          <h2 className="text-lg font-semibold mb-4" style={{ color: 'var(--color-text-primary)' }}>
            Patient Information
          </h2>
          <div className="space-y-4">
            {patient.date_of_birth && (
              <div className="flex items-center gap-3" style={{ color: 'var(--color-text-secondary)' }}>
                <Calendar className="w-5 h-5" style={{ color: 'var(--color-text-muted)' }} />
                <span>{format(new Date(patient.date_of_birth), 'MMM d, yyyy')}</span>
              </div>
            )}
            {patient.phone && (
              <div className="flex items-center gap-3" style={{ color: 'var(--color-text-secondary)' }}>
                <Phone className="w-5 h-5" style={{ color: 'var(--color-text-muted)' }} />
                <span>{patient.phone}</span>
              </div>
            )}
            {patient.email && (
              <div className="flex items-center gap-3" style={{ color: 'var(--color-text-secondary)' }}>
                <Mail className="w-5 h-5" style={{ color: 'var(--color-text-muted)' }} />
                <span>{patient.email}</span>
              </div>
            )}
            {patient.gender && (
              <div style={{ color: 'var(--color-text-secondary)' }}>
                <span style={{ color: 'var(--color-text-muted)' }}>Gender:</span> {patient.gender}
              </div>
            )}
          </div>
        </div>

        {/* Triage threads */}
        <div className="lg:col-span-2 card">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold" style={{ color: 'var(--color-text-primary)' }}>
              Triage History
            </h2>
            <button
              onClick={() => setShowNewTriage(true)}
              className="btn-primary flex items-center gap-2 text-sm"
            >
              <Plus className="w-4 h-4" />
              New Triage
            </button>
          </div>

          {threadsLoading ? (
            <div className="flex items-center justify-center py-8">
              <Activity className="w-6 h-6 text-primary-500 animate-spin" />
            </div>
          ) : threads.length === 0 ? (
            <div className="text-center py-8">
              <MessageSquare className="w-12 h-12 mx-auto mb-3" style={{ color: 'var(--color-text-muted)' }} />
              <p style={{ color: 'var(--color-text-secondary)' }}>No triage sessions yet</p>
            </div>
          ) : (
            <div className="space-y-3">
              {threads.map((thread: any) => (
                <Link
                  key={thread.id}
                  to={`/triage/${thread.id}`}
                  className="block p-4 rounded-lg transition-all hover:border-primary-500/50"
                  style={{ 
                    backgroundColor: 'var(--color-bg-tertiary)',
                    border: '1px solid var(--color-border)'
                  }}
                >
                  <div className="flex items-start justify-between">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        {getStatusBadge(thread.status)}
                        {thread.status === 'EMERGENCY' && (
                          <AlertTriangle className="w-4 h-4 text-emergency-400" />
                        )}
                      </div>
                      {thread.chief_complaint && (
                        <p className="text-sm line-clamp-1" style={{ color: 'var(--color-text-secondary)' }}>
                          {thread.chief_complaint}
                        </p>
                      )}
                    </div>
                    <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
                      {format(new Date(thread.created_at), 'MMM d, HH:mm')}
                    </span>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* New Triage Modal */}
      {showNewTriage && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="card w-full max-w-md animate-slide-up" style={{ backgroundColor: 'var(--color-card)' }}>
            <h2 className="text-xl font-semibold mb-4" style={{ color: 'var(--color-text-primary)' }}>
              Start New Triage
            </h2>
            <div className="space-y-4">
              <div>
                <label 
                  className="block text-sm font-medium mb-2"
                  style={{ color: 'var(--color-text-secondary)' }}
                >
                  Chief Complaint (optional)
                </label>
                <textarea
                  value={chiefComplaint}
                  onChange={(e) => setChiefComplaint(e.target.value)}
                  className="input-field min-h-[100px] resize-none"
                  placeholder="What brings the patient in today?"
                />
              </div>
              <div className="flex gap-3">
                <button
                  type="button"
                  onClick={() => {
                    setShowNewTriage(false)
                    setChiefComplaint('')
                  }}
                  className="flex-1 btn-secondary"
                >
                  Cancel
                </button>
                <button
                  onClick={() => createThreadMutation.mutate()}
                  disabled={createThreadMutation.isPending}
                  className="flex-1 btn-primary disabled:opacity-50"
                >
                  {createThreadMutation.isPending ? 'Starting...' : 'Start Triage'}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
