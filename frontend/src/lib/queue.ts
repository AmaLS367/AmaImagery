export type Task<T=any> = (signal: AbortSignal) => Promise<T>

export class RequestQueue {
  private max: number
  private active = 0
  private q: Array<{ fn: Task, resolve: (v:any)=>void, reject:(e:any)=>void, controller: AbortController }> = []
  private cancelPrev: boolean

  constructor(maxParallel = 1, cancelPrevious = true) {
    this.max = Math.max(1, Math.min(3, maxParallel))
    this.cancelPrev = cancelPrevious
  }

  setPolicy(maxParallel: number, cancelPrevious: boolean) {
    this.max = Math.max(1, Math.min(3, maxParallel))
    this.cancelPrev = cancelPrevious
  }

  run<T>(fn: Task<T>): { promise: Promise<T>, abort: () => void } {
    const controller = new AbortController()
    const p = new Promise<T>((resolve, reject) => {
  // If cancelPrev is enabled, abort existing queued tasks first,
  // then push the new task. Previously abortAll() ran after pushing
  // which aborted the newly added task as well.
  if (this.cancelPrev) this.abortAll()
  this.q.push({ fn, resolve, reject, controller })
  this.pump()
    })
    return { promise: p, abort: () => controller.abort() }
  }

  private pump() {
    while (this.active < this.max && this.q.length) {
      const item = this.q.shift()!
      this.active++
      item.fn(item.controller.signal).then(
        (v) => { this.active--; item.resolve(v); this.pump() },
        (e) => { this.active--; item.reject(e); this.pump() },
      )
    }
  }

  abortAll() {
    for (const it of this.q) it.controller.abort()
    this.q = []
  }
}
