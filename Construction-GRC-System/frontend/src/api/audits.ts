import type { Audit, AuditCreate, Finding } from '@/types'
import client from './client'

export const auditsApi = {
  list(status?: string): Promise<Audit[]> {
    const params = status ? { status } : {}
    return client.get<Audit[]>('/audits/', { params }).then((r) => r.data)
  },

  get(id: string): Promise<Audit> {
    return client.get<Audit>(`/audits/${id}/`).then((r) => r.data)
  },

  create(data: AuditCreate): Promise<Audit> {
    return client.post<Audit>('/audits/', data).then((r) => r.data)
  },

  update(id: string, data: AuditCreate): Promise<Audit> {
    return client.put<Audit>(`/audits/${id}/`, data).then((r) => r.data)
  },

  delete(id: string): Promise<void> {
    return client.delete(`/audits/${id}/`).then(() => undefined)
  },

  listFindings(auditId: string, severity?: string): Promise<Finding[]> {
    const params = severity ? { severity } : {}
    return client
      .get<Finding[]>(`/audits/${auditId}/findings/`, { params })
      .then((r) => r.data)
  },

  createFinding(auditId: string, data: { title: string; severity: string; description?: string }): Promise<Finding> {
    return client.post<Finding>(`/audits/${auditId}/findings/`, data).then((r) => r.data)
  },
}
