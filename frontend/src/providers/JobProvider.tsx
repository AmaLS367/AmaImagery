import React, { createContext, useContext, useEffect, useMemo, useRef, useState } from 'react'
import { generateJSON, getTaskStatus, type GeneratePayload, type TaskResp, type TaskStatusResp } from '../lib/api'
import { RequestQueue } from '../lib/queue'
import { addHistory, type HistoryItem } from '../lib/storage'
import { guessNSFW } from '../lib/nsfw'
import { useSettings } from './SettingsProvider' 

export type JobStatus = 'queued' | 'running' | 'completed' | 'error' | 'canceled'
export type Job = {
  id: string
  task_id?: string
  status: JobStatus
  payload: GeneratePayload
  result?: TaskStatusResp
  error?: string
  startedAt: number
  finishedAt?: number
}

type Ctx = {
  jobs: Job[]
  start: (payload: GeneratePayload) => string
  cancel: (id: string) => void
  get: (id: string | null) => Job | undefined
  anyRunning: boolean
}

const JobCtx = createContext<Ctx | null>(null)

function beep() {
  try {
    const ctx = new (window.AudioContext || (window as any).webkitAudioContext)()
    const o = ctx.createOscillator()
    const g = ctx.createGain()
    o.type = 'sine'; o.frequency.value = 880
    o.connect(g); g.connect(ctx.destination)
    g.gain.setValueAtTime(0.001, ctx.currentTime)
    g.gain.exponentialRampToValueAtTime(0.1, ctx.currentTime + 0.02)
    o.start(); o.stop(ctx.currentTime + 0.15)
  } catch {}
}

export function JobProvider({ children }: { children: React.ReactNode }) {
  const { settings } = useSettings()
  const [jobs, setJobs] = useState<Job[]>([])
  const abortMap = useRef<Map<string, () => void>>(new Map())

  // Единая очередь запросов живёт тут, не в странице
  const queueRef = useRef(new RequestQueue(settings.queue.maxParallel, settings.queue.cancelPrevious))

  // При изменении политики очереди — обновить
  useEffect(() => {
    queueRef.current.setPolicy(settings.queue.maxParallel, settings.queue.cancelPrevious)
  }, [settings.queue.maxParallel, settings.queue.cancelPrevious])

  const start = (payload: GeneratePayload) => {
    if (settings.queue.cancelPrevious) {
      // отменяем старые задачи
      abortMap.current.forEach(fn => fn())
      abortMap.current.clear()
      setJobs(prev => prev.map(j => j.status === 'running' || j.status === 'queued' ? { ...j, status: 'canceled' } : j))
    }

    const id = (typeof crypto !== 'undefined' && 'randomUUID' in crypto)
      ? crypto.randomUUID()
      : `job_${Date.now()}_${Math.random().toString(36).slice(2)}`

    const job: Job = { id, status: 'queued', payload, startedAt: Date.now() }
    setJobs(prev => [job, ...prev])

    const { promise, abort } = queueRef.current.run(async (signal) => {
      // Отправляем запрос на генерацию
      const taskResp: TaskResp = await generateJSON(payload, signal)
      const task_id = taskResp.task_id

      // Обновляем job с task_id
      setJobs(prev => prev.map(j => j.id === id ? { ...j, task_id, status: 'running' } : j))

      // Polling статуса задачи
      const pollInterval = 2000 // 2 секунды
      const maxAttempts = 300 // максимум 10 минут (300 * 2 сек)
      const queuedTimeout = 120000 // 2 минуты для статуса "queued" (если worker не запущен)
      let attempts = 0
      let queuedStartTime: number | null = null

      while (attempts < maxAttempts && !signal.aborted) {
        await new Promise(resolve => setTimeout(resolve, pollInterval))
        
        if (signal.aborted) {
          setJobs(prev => prev.map(j => j.id === id ? { ...j, status: 'canceled', finishedAt: Date.now() } : j))
          return
        }

        try {
          const statusResp = await getTaskStatus(task_id, signal)
          
          // Check if task is completed - can use image_path, image_filename, or image_url
          const hasImage = statusResp.image_path || statusResp.image_filename || statusResp.image_url
          
          if (statusResp.status === 'completed' && hasImage) {
            // Задача завершена успешно
            setJobs(prev => prev.map(j => j.id === id ? { 
              ...j, 
              status: 'completed', 
              result: statusResp, 
              finishedAt: Date.now() 
            } : j))

            // В историю
            const hist: HistoryItem = {
              prompt: payload.prompt,
              neg: payload.negative_prompt || '',
              steps: payload.steps,
              guidance: payload.guidance_scale,
              width: payload.width,
              height: payload.height,
              seed: payload.seed,
              ipScale: payload.ip_scale ?? 0.6,
              path: statusResp.image_path || '',
              ts: Date.now(),
              tags: [],
              pinned: false,
              nsfw: guessNSFW(payload.prompt, payload.negative_prompt || ''),
              exp: statusResp.exp || undefined,
              sig: statusResp.sig || undefined,
            }
            addHistory(hist)

            // Уведомления/звук
            if (settings.notifyOnDone && 'Notification' in window) {
              try {
                if (Notification.permission !== 'granted') await Notification.requestPermission()
                if (Notification.permission === 'granted') new Notification('Готово', { body: 'Изображение сгенерировано' })
              } catch {}
            }
            if (settings.soundOnDone) beep()
            return
          } else if (statusResp.status === 'failed') {
            // Задача провалилась
            const errorMsg = statusResp.error || 'Generation failed'
            setJobs(prev => prev.map(j => j.id === id ? { 
              ...j, 
              status: 'error', 
              error: errorMsg, 
              finishedAt: Date.now() 
            } : j))
            return
          } else if (statusResp.status === 'queued') {
            // Отслеживаем время в статусе "queued"
            if (queuedStartTime === null) {
              queuedStartTime = Date.now()
            } else if (Date.now() - queuedStartTime > queuedTimeout) {
              // Задача слишком долго в очереди - вероятно worker не запущен
              setJobs(prev => prev.map(j => j.id === id ? { 
                ...j, 
                status: 'error', 
                error: 'Task stuck in queue. Worker may not be running.', 
                finishedAt: Date.now() 
              } : j))
              return
            }
          } else if (statusResp.status === 'running') {
            // Сбрасываем таймер, если задача начала выполняться
            queuedStartTime = null
          }
          // Продолжаем polling для статусов 'queued' и 'running'
        } catch (e: any) {
          if (e?.name === 'AbortError') {
            setJobs(prev => prev.map(j => j.id === id ? { ...j, status: 'canceled', finishedAt: Date.now() } : j))
            return
          }
          // Ошибка при получении статуса - продолжаем попытки
          console.warn('Failed to get task status:', e)
        }

        attempts++
      }

      // Timeout
      if (attempts >= maxAttempts) {
        setJobs(prev => prev.map(j => j.id === id ? { 
          ...j, 
          status: 'error', 
          error: 'Generation timeout', 
          finishedAt: Date.now() 
        } : j))
      }
    })

    abortMap.current.set(id, abort)

    promise.catch((e: any) => {
      if (e?.name === 'AbortError') {
        setJobs(prev => prev.map(j => j.id === id ? { ...j, status: 'canceled', finishedAt: Date.now() } : j))
      } else {
        setJobs(prev => prev.map(j => j.id === id ? { ...j, status: 'error', error: e?.message || String(e), finishedAt: Date.now() } : j))
      }
    }).finally(() => {
      abortMap.current.delete(id)
    })

    return id
  }

  const cancel = (id: string) => {
    const fn = abortMap.current.get(id)
    if (fn) fn()
  }

  const get = (id: string | null) => jobs.find(j => j.id === id || false)

  const ctx = useMemo<Ctx>(() => ({
    jobs,
    start,
    cancel,
    get,
    anyRunning: jobs.some(j => j.status === 'running' || j.status === 'queued'),
  }), [jobs])

  return <JobCtx.Provider value={ctx}>{children}</JobCtx.Provider>
}

export function useJobs() {
  const v = useContext(JobCtx)
  if (!v) throw new Error('JobProvider is missing')
  return v
}
