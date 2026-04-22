import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Plus, Search, Users, Activity, X } from 'lucide-react'
import { patientsApi } from '../api/client'

interface NewPatientForm {
  first_name: string
  last_name: string
  date_of_birth: string
  gender: string
  phone: string
  email: string
}

export default function PatientsPage() {
  const queryClient = useQueryClient()
  const [showModal, setShowModal] = useState(false)
  const [search, setSearch] = useState('')
  const [formData, setFormData] = useState<NewPatientForm>({
    first_name: '',
    last_name: '',
    date_of_birth: '',
    gender: '',
    phone: '',
    email: '',
  })

  const { data, isLoading } = useQuery({
    queryKey: ['patients'],
    queryFn: () => patientsApi.list({ limit: 100 }),
  })

  const createMutation = useMutation({
    mutationFn: (data: NewPatientForm) => patientsApi.create(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['patients'] })
      setShowModal(false)
      setFormData({
        first_name: '',
        last_name: '',
        date_of_birth: '',
        gender: '',
        phone: '',
        email: '',
      })
    },
  })

  const patients = data?.data || []
  const filteredPatients = patients.filter((p: any) =>
    `${p.first_name} ${p.last_name}`.toLowerCase().includes(search.toLowerCase())
  )

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    createMutation.mutate(formData)
  }

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <Search 
            className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5" 
            style={{ color: 'var(--color-text-muted)' }} 
          />
          <input
            type="text"
            placeholder="Search patients..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input-field pl-12"
          />
        </div>
        <button
          onClick={() => setShowModal(true)}
          className="btn-primary flex items-center gap-2"
        >
          <Plus className="w-5 h-5" />
          Add Patient
        </button>
      </div>

      {/* Patients list */}
      <div className="card">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Activity className="w-8 h-8 text-primary-500 animate-spin" />
          </div>
        ) : filteredPatients.length === 0 ? (
          <div className="text-center py-12">
            <Users className="w-16 h-16 mx-auto mb-4" style={{ color: 'var(--color-text-muted)' }} />
            <p className="text-xl font-medium" style={{ color: 'var(--color-text-secondary)' }}>No patients found</p>
            <p className="mt-2" style={{ color: 'var(--color-text-muted)' }}>
              {search ? 'Try a different search term' : 'Add your first patient to get started'}
            </p>
          </div>
        ) : (
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
            {filteredPatients.map((patient: any) => (
              <Link
                key={patient.id}
                to={`/patients/${patient.id}`}
                className="p-4 rounded-lg transition-all group hover:border-primary-500/50"
                style={{ 
                  backgroundColor: 'var(--color-bg-tertiary)',
                  border: '1px solid var(--color-border)'
                }}
              >
                <div className="flex items-center gap-4">
                  <div className="w-12 h-12 rounded-full bg-gradient-to-br from-primary-500 to-primary-700 flex items-center justify-center text-white font-semibold">
                    {patient.first_name[0]}{patient.last_name[0]}
                  </div>
                  <div className="min-w-0">
                    <p 
                      className="font-medium group-hover:text-primary-500 transition-colors"
                      style={{ color: 'var(--color-text-primary)' }}
                    >
                      {patient.first_name} {patient.last_name}
                    </p>
                    {patient.email && (
                      <p className="text-sm truncate" style={{ color: 'var(--color-text-muted)' }}>
                        {patient.email}
                      </p>
                    )}
                  </div>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>

      {/* Add Patient Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div 
            className="card w-full max-w-md max-h-[90vh] overflow-auto animate-slide-up"
            style={{ backgroundColor: 'var(--color-card)' }}
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold" style={{ color: 'var(--color-text-primary)' }}>
                Add New Patient
              </h2>
              <button
                onClick={() => setShowModal(false)}
                className="p-2 rounded-lg hover:bg-[var(--color-bg-hover)]"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label 
                    className="block text-sm font-medium mb-2"
                    style={{ color: 'var(--color-text-secondary)' }}
                  >
                    First Name *
                  </label>
                  <input
                    type="text"
                    value={formData.first_name}
                    onChange={(e) => setFormData({ ...formData, first_name: e.target.value })}
                    className="input-field"
                    required
                  />
                </div>
                <div>
                  <label 
                    className="block text-sm font-medium mb-2"
                    style={{ color: 'var(--color-text-secondary)' }}
                  >
                    Last Name *
                  </label>
                  <input
                    type="text"
                    value={formData.last_name}
                    onChange={(e) => setFormData({ ...formData, last_name: e.target.value })}
                    className="input-field"
                    required
                  />
                </div>
              </div>

              <div>
                <label 
                  className="block text-sm font-medium mb-2"
                  style={{ color: 'var(--color-text-secondary)' }}
                >
                  Date of Birth
                </label>
                <input
                  type="date"
                  value={formData.date_of_birth}
                  onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
                  className="input-field"
                />
              </div>

              <div>
                <label 
                  className="block text-sm font-medium mb-2"
                  style={{ color: 'var(--color-text-secondary)' }}
                >
                  Gender
                </label>
                <select
                  value={formData.gender}
                  onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
                  className="input-field"
                >
                  <option value="">Select...</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                  <option value="other">Other</option>
                </select>
              </div>

              <div>
                <label 
                  className="block text-sm font-medium mb-2"
                  style={{ color: 'var(--color-text-secondary)' }}
                >
                  Phone
                </label>
                <input
                  type="tel"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  className="input-field"
                  placeholder="(555) 123-4567"
                />
              </div>

              <div>
                <label 
                  className="block text-sm font-medium mb-2"
                  style={{ color: 'var(--color-text-secondary)' }}
                >
                  Email
                </label>
                <input
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  className="input-field"
                  placeholder="patient@email.com"
                />
              </div>

              <div className="flex gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="flex-1 btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={createMutation.isPending}
                  className="flex-1 btn-primary disabled:opacity-50"
                >
                  {createMutation.isPending ? 'Creating...' : 'Create Patient'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  )
}
