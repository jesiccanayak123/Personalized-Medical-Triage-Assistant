import { useState, useRef, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { 
  ArrowLeft, 
  Send, 
  Activity, 
  AlertTriangle,
  FileText,
  CheckCircle,
  X
} from 'lucide-react'
import { triageApi } from '../api/client'
import clsx from 'clsx'

interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}

export default function TriageChatPage() {
  const { threadId } = useParams<{ threadId: string }>()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const [input, setInput] = useState('')
  const [showArtifacts, setShowArtifacts] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const { data: threadData, isLoading: threadLoading } = useQuery({
    queryKey: ['thread', threadId],
    queryFn: () => triageApi.getThread(threadId!),
    enabled: !!threadId,
  })

  const { data: messagesData, isLoading: messagesLoading } = useQuery({
    queryKey: ['messages', threadId],
    queryFn: () => triageApi.getMessages(threadId!),
    enabled: !!threadId,
    refetchInterval: threadData?.data?.status === 'DONE' ? false : 5000,
  })

  const { data: artifactsData } = useQuery({
    queryKey: ['artifacts', threadId],
    queryFn: () => triageApi.getArtifacts(threadId!),
    enabled: !!threadId && (threadData?.data?.status === 'DONE' || threadData?.data?.status === 'EMERGENCY'),
  })

  const sendMutation = useMutation({
    mutationFn: (content: string) => triageApi.sendMessage(threadId!, content),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['messages', threadId] })
      queryClient.invalidateQueries({ queryKey: ['thread', threadId] })
      setInput('')
    },
  })

  const thread = threadData?.data
  const messages: Message[] = messagesData?.data || []
  const artifacts = artifactsData?.data || {}

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || sendMutation.isPending) return
    sendMutation.mutate(input.trim())
  }

  const isEmergency = thread?.status === 'EMERGENCY'
  const isDone = thread?.status === 'DONE'

  if (threadLoading) {
    return (
      <div className="flex items-center justify-center h-full">
        <Activity className="w-8 h-8 text-primary-500 animate-spin" />
      </div>
    )
  }

  if (!thread) {
    return (
      <div className="text-center py-16">
        <p style={{ color: 'var(--color-text-secondary)' }}>Thread not found</p>
        <button onClick={() => navigate(-1)} className="btn-primary mt-4">
          Go Back
        </button>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] animate-fade-in">
      {/* Emergency banner */}
      {isEmergency && (
        <div className="bg-emergency-900/80 border border-emergency-700 rounded-lg p-4 mb-4 flex items-start gap-3">
          <AlertTriangle className="w-6 h-6 text-emergency-400 flex-shrink-0" />
          <div>
            <h3 className="font-semibold text-emergency-300">Emergency Detected</h3>
            <p className="text-sm text-emergency-400 mt-1">
              Critical symptoms have been detected. Please seek immediate medical attention.
              Call 911 or go to the nearest emergency room.
            </p>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(-1)}
            className="p-2 rounded-lg hover:bg-[var(--color-bg-hover)]"
            style={{ color: 'var(--color-text-secondary)' }}
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-lg font-semibold" style={{ color: 'var(--color-text-primary)' }}>
              Triage Session
            </h1>
            <div className="flex items-center gap-2 mt-1">
              <span className={clsx(
                'status-badge',
                isEmergency ? 'bg-emergency-500/20 text-emergency-600 dark:text-emergency-300 border-emergency-500/30' :
                isDone ? 'bg-success-500/20 text-success-600 dark:text-success-300 border-success-500/30' :
                'bg-primary-500/20 text-primary-600 dark:text-primary-300 border-primary-500/30'
              )}>
                {thread.status}
              </span>
              {thread.missing_fields?.length > 0 && !isDone && (
                <span className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
                  {thread.missing_fields.length} fields remaining
                </span>
              )}
            </div>
          </div>
        </div>

        {(isDone || isEmergency) && Object.keys(artifacts).length > 0 && (
          <button
            onClick={() => setShowArtifacts(true)}
            className="btn-secondary flex items-center gap-2"
          >
            <FileText className="w-4 h-4" />
            View Summary
          </button>
        )}
      </div>

      {/* Messages */}
      <div 
        className="flex-1 overflow-y-auto rounded-xl p-4"
        style={{ 
          backgroundColor: 'var(--color-bg-tertiary)',
          border: '1px solid var(--color-border)'
        }}
      >
        {messagesLoading ? (
          <div className="flex items-center justify-center h-full">
            <Activity className="w-6 h-6 text-primary-500 animate-spin" />
          </div>
        ) : messages.length === 0 ? (
          <div 
            className="flex items-center justify-center h-full"
            style={{ color: 'var(--color-text-muted)' }}
          >
            Start the conversation by describing your symptoms
          </div>
        ) : (
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={clsx(
                  'flex',
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                )}
              >
                <div
                  className={clsx(
                    'max-w-[80%] rounded-2xl px-4 py-3',
                    message.role === 'user'
                      ? 'bg-primary-600 text-white rounded-br-md'
                      : 'rounded-bl-md'
                  )}
                  style={message.role === 'assistant' ? {
                    backgroundColor: 'var(--color-bg-hover)',
                    color: 'var(--color-text-primary)'
                  } : undefined}
                >
                  <p className="whitespace-pre-wrap">{message.content}</p>
                </div>
              </div>
            ))}
            {sendMutation.isPending && (
              <div className="flex justify-start">
                <div 
                  className="rounded-2xl rounded-bl-md px-4 py-3"
                  style={{ backgroundColor: 'var(--color-bg-hover)' }}
                >
                  <Activity className="w-5 h-5 text-primary-500 animate-spin" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="mt-4">
        <div className="flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={isDone ? "This session has ended" : "Describe your symptoms..."}
            className="input-field flex-1"
            disabled={isDone || isEmergency || sendMutation.isPending}
          />
          <button
            type="submit"
            disabled={!input.trim() || isDone || isEmergency || sendMutation.isPending}
            className="btn-primary px-6 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
        {thread.missing_fields?.length > 0 && !isDone && !isEmergency && (
          <p className="text-xs mt-2" style={{ color: 'var(--color-text-muted)' }}>
            Still gathering: {thread.missing_fields.join(', ')}
          </p>
        )}
      </form>

      {/* Artifacts Modal */}
      {showArtifacts && (
        <div className="fixed inset-0 bg-black/70 flex items-center justify-center z-50 p-4">
          <div 
            className="card w-full max-w-2xl max-h-[90vh] overflow-auto animate-slide-up"
            style={{ backgroundColor: 'var(--color-card)' }}
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold" style={{ color: 'var(--color-text-primary)' }}>
                Triage Summary
              </h2>
              <button
                onClick={() => setShowArtifacts(false)}
                className="p-2 rounded-lg hover:bg-[var(--color-bg-hover)]"
                style={{ color: 'var(--color-text-secondary)' }}
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-6">
              {/* Risk Assessment */}
              {artifacts.risk_assessment && (
                <div>
                  <h3 
                    className="text-lg font-medium mb-3 flex items-center gap-2"
                    style={{ color: 'var(--color-text-primary)' }}
                  >
                    <AlertTriangle className="w-5 h-5 text-yellow-500" />
                    Risk Assessment
                  </h3>
                  <div 
                    className="rounded-lg p-4"
                    style={{ backgroundColor: 'var(--color-bg-tertiary)' }}
                  >
                    <p style={{ color: 'var(--color-text-secondary)' }}>
                      Disposition: <span className="font-medium" style={{ color: 'var(--color-text-primary)' }}>
                        {artifacts.risk_assessment.disposition}
                      </span>
                    </p>
                    {artifacts.risk_assessment.red_flags?.length > 0 && (
                      <div className="mt-2">
                        <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>Red Flags:</p>
                        <ul className="list-disc list-inside text-sm text-emergency-400 mt-1">
                          {artifacts.risk_assessment.red_flags.map((flag: any, i: number) => (
                            <li key={i}>{flag.label}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* ICD-10 Codes */}
              {artifacts.icd10_coding?.codes?.length > 0 && (
                <div>
                  <h3 
                    className="text-lg font-medium mb-3 flex items-center gap-2"
                    style={{ color: 'var(--color-text-primary)' }}
                  >
                    <FileText className="w-5 h-5 text-primary-500" />
                    ICD-10 Codes
                  </h3>
                  <div className="space-y-2">
                    {artifacts.icd10_coding.codes.map((code: any, i: number) => (
                      <div 
                        key={i} 
                        className="rounded-lg p-4"
                        style={{ backgroundColor: 'var(--color-bg-tertiary)' }}
                      >
                        <div className="flex items-center justify-between">
                          <span className="font-mono text-primary-500">{code.icd10}</span>
                          <span className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
                            {(code.confidence * 100).toFixed(0)}% confidence
                          </span>
                        </div>
                        <p className="mt-1" style={{ color: 'var(--color-text-secondary)' }}>
                          {code.description}
                        </p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* SOAP Note */}
              {artifacts.soap_note && (
                <div>
                  <h3 
                    className="text-lg font-medium mb-3 flex items-center gap-2"
                    style={{ color: 'var(--color-text-primary)' }}
                  >
                    <CheckCircle className="w-5 h-5 text-success-500" />
                    SOAP Note
                  </h3>
                  <div 
                    className="rounded-lg p-4 space-y-6"
                    style={{ backgroundColor: 'var(--color-bg-tertiary)' }}
                  >
                    {/* Subjective */}
                    <div>
                      <h4 className="text-sm font-semibold text-primary-500 uppercase tracking-wider mb-3">
                        Subjective
                      </h4>
                      <div className="space-y-3">
                        <div>
                          <span className="text-sm" style={{ color: 'var(--color-text-muted)' }}>Chief Complaint:</span>
                          <p style={{ color: 'var(--color-text-primary)' }}>
                            {artifacts.soap_note.subjective?.chief_complaint || 'N/A'}
                          </p>
                        </div>
                        {artifacts.soap_note.subjective?.history_of_present_illness && (
                          <div>
                            <span className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
                              History of Present Illness:
                            </span>
                            {typeof artifacts.soap_note.subjective.history_of_present_illness === 'string' ? (
                              <p className="mt-1" style={{ color: 'var(--color-text-secondary)' }}>
                                {artifacts.soap_note.subjective.history_of_present_illness}
                              </p>
                            ) : (
                              <ul className="mt-1 space-y-1">
                                {Object.entries(artifacts.soap_note.subjective.history_of_present_illness).map(([key, value]) => (
                                  <li key={key} className="flex">
                                    <span className="capitalize w-32 flex-shrink-0" style={{ color: 'var(--color-text-muted)' }}>
                                      {key.replace(/_/g, ' ')}:
                                    </span>
                                    <span style={{ color: 'var(--color-text-secondary)' }}>
                                      {Array.isArray(value) ? (value as string[]).join(', ') : String(value)}
                                    </span>
                                  </li>
                                ))}
                              </ul>
                            )}
                          </div>
                        )}
                        {artifacts.soap_note.subjective?.review_of_systems && (
                          <div>
                            <span className="text-sm" style={{ color: 'var(--color-text-muted)' }}>
                              Review of Systems:
                            </span>
                            {typeof artifacts.soap_note.subjective.review_of_systems === 'string' ? (
                              <p className="mt-1" style={{ color: 'var(--color-text-secondary)' }}>
                                {artifacts.soap_note.subjective.review_of_systems}
                              </p>
                            ) : (
                              <ul className="mt-1 space-y-1">
                                {Object.entries(artifacts.soap_note.subjective.review_of_systems).map(([system, symptoms]) => (
                                  <li key={system} className="flex">
                                    <span className="capitalize w-32 flex-shrink-0" style={{ color: 'var(--color-text-muted)' }}>
                                      {system}:
                                    </span>
                                    <span style={{ color: 'var(--color-text-secondary)' }}>
                                      {Array.isArray(symptoms) ? (symptoms as string[]).join(', ') : String(symptoms)}
                                    </span>
                                  </li>
                                ))}
                              </ul>
                            )}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Objective */}
                    <div>
                      <h4 className="text-sm font-semibold text-primary-500 uppercase tracking-wider mb-3">
                        Objective
                      </h4>
                      <div className="space-y-2">
                        {artifacts.soap_note.objective?.vitals && (
                          <div>
                            <span className="text-sm" style={{ color: 'var(--color-text-muted)' }}>Vitals:</span>
                            {typeof artifacts.soap_note.objective.vitals === 'string' ? (
                              <p className="mt-1" style={{ color: 'var(--color-text-secondary)' }}>
                                {artifacts.soap_note.objective.vitals}
                              </p>
                            ) : (
                              <ul className="mt-1">
                                {Object.entries(artifacts.soap_note.objective.vitals).map(([key, value]) => (
                                  <li key={key} className="flex">
                                    <span className="capitalize w-32 flex-shrink-0" style={{ color: 'var(--color-text-muted)' }}>
                                      {key.replace(/_/g, ' ')}:
                                    </span>
                                    <span style={{ color: 'var(--color-text-secondary)' }}>{String(value)}</span>
                                  </li>
                                ))}
                              </ul>
                            )}
                          </div>
                        )}
                        {artifacts.soap_note.objective?.physical_exam_findings && (
                          <div>
                            <span className="text-sm" style={{ color: 'var(--color-text-muted)' }}>Physical Exam:</span>
                            {typeof artifacts.soap_note.objective.physical_exam_findings === 'string' ? (
                              <p className="mt-1" style={{ color: 'var(--color-text-secondary)' }}>
                                {artifacts.soap_note.objective.physical_exam_findings}
                              </p>
                            ) : (
                              <ul className="mt-1">
                                {Object.entries(artifacts.soap_note.objective.physical_exam_findings).map(([key, value]) => (
                                  <li key={key} className="flex">
                                    <span className="capitalize w-32 flex-shrink-0" style={{ color: 'var(--color-text-muted)' }}>
                                      {key}:
                                    </span>
                                    <span style={{ color: 'var(--color-text-secondary)' }}>{String(value)}</span>
                                  </li>
                                ))}
                              </ul>
                            )}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Assessment */}
                    <div>
                      <h4 className="text-sm font-semibold text-primary-500 uppercase tracking-wider mb-3">
                        Assessment
                      </h4>
                      <div className="space-y-2">
                        {artifacts.soap_note.assessment?.working_diagnosis && (
                          <div>
                            <span className="text-sm" style={{ color: 'var(--color-text-muted)' }}>Working Diagnosis:</span>
                            <p style={{ color: 'var(--color-text-primary)' }}>
                              {artifacts.soap_note.assessment.working_diagnosis}
                            </p>
                          </div>
                        )}
                        {(artifacts.soap_note.assessment?.icd_10_codes || artifacts.soap_note.assessment?.['ICD-10_codes']) && (
                          <div>
                            <span className="text-sm" style={{ color: 'var(--color-text-muted)' }}>ICD-10 Codes:</span>
                            <p className="text-primary-500 font-mono">
                              {(() => {
                                const codes = artifacts.soap_note.assessment.icd_10_codes || artifacts.soap_note.assessment['ICD-10_codes'];
                                return Array.isArray(codes) ? codes.join(', ') : codes;
                              })()}
                            </p>
                          </div>
                        )}
                        {artifacts.soap_note.assessment?.differential_diagnosis && (
                          <div>
                            <span className="text-sm" style={{ color: 'var(--color-text-muted)' }}>Differential Diagnosis:</span>
                            {Array.isArray(artifacts.soap_note.assessment.differential_diagnosis) ? (
                              <ul className="mt-1 list-disc list-inside" style={{ color: 'var(--color-text-secondary)' }}>
                                {artifacts.soap_note.assessment.differential_diagnosis.map((dx: string, i: number) => (
                                  <li key={i}>{dx}</li>
                                ))}
                              </ul>
                            ) : (
                              <p className="mt-1" style={{ color: 'var(--color-text-secondary)' }}>
                                {artifacts.soap_note.assessment.differential_diagnosis}
                              </p>
                            )}
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Plan */}
                    <div>
                      <h4 className="text-sm font-semibold text-primary-500 uppercase tracking-wider mb-3">
                        Plan
                      </h4>
                      <div className="space-y-2">
                        {artifacts.soap_note.plan?.treatment_recommendations && (
                          <div>
                            <span className="text-sm" style={{ color: 'var(--color-text-muted)' }}>Treatment:</span>
                            {Array.isArray(artifacts.soap_note.plan.treatment_recommendations) ? (
                              <ul className="mt-1 list-disc list-inside" style={{ color: 'var(--color-text-secondary)' }}>
                                {artifacts.soap_note.plan.treatment_recommendations.map((rec: string, i: number) => (
                                  <li key={i}>{rec}</li>
                                ))}
                              </ul>
                            ) : (
                              <p className="mt-1" style={{ color: 'var(--color-text-secondary)' }}>
                                {artifacts.soap_note.plan.treatment_recommendations}
                              </p>
                            )}
                          </div>
                        )}
                        {artifacts.soap_note.plan?.medications && (
                          <div>
                            <span className="text-sm" style={{ color: 'var(--color-text-muted)' }}>Medications:</span>
                            {Array.isArray(artifacts.soap_note.plan.medications) ? (
                              <ul className="mt-1 list-disc list-inside" style={{ color: 'var(--color-text-secondary)' }}>
                                {artifacts.soap_note.plan.medications.map((med: string, i: number) => (
                                  <li key={i}>{med}</li>
                                ))}
                              </ul>
                            ) : (
                              <p className="mt-1" style={{ color: 'var(--color-text-secondary)' }}>
                                {artifacts.soap_note.plan.medications}
                              </p>
                            )}
                          </div>
                        )}
                        {artifacts.soap_note.plan?.['follow-up_instructions'] && (
                          <div>
                            <span className="text-sm" style={{ color: 'var(--color-text-muted)' }}>Follow-up:</span>
                            <p style={{ color: 'var(--color-text-primary)' }}>
                              {artifacts.soap_note.plan['follow-up_instructions']}
                            </p>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
