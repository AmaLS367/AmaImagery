export type AppErrorCode =
  | 'validation' | 'unauthorized' | 'forbidden' | 'not_found' | 'wrong_method'
  | 'timeout' | 'conflict' | 'payload_too_large' | 'unsupported_media'
  | 'rate_limit' | 'network' | 'server' | 'unknown'

export type AppError = {
  http: number | 0
  code: AppErrorCode
  fieldErrors?: Record<string, string>
  retryAfter?: number
  raw?: unknown
}

export function normalizeError(input: any): AppError {
  if (input instanceof TypeError) {
    return { http: 0, code: 'network', raw: input }
  }
  if (input && typeof input === 'object' && 'status' in input && typeof (input as any).status === 'number') {
    const res = input as Response
    const http = res.status
    let code: AppErrorCode = 'unknown'
    if (http === 400 || http === 422) code = 'validation'
    else if (http === 401) code = 'unauthorized'
    else if (http === 403) code = 'forbidden'
    else if (http === 404) code = 'not_found'
    else if (http === 405) code = 'wrong_method'
    else if (http === 408 || http === 504) code = 'timeout'
    else if (http === 409) code = 'conflict'
    else if (http === 413) code = 'payload_too_large'
    else if (http === 415) code = 'unsupported_media'
    else if (http === 429) code = 'rate_limit'
    else if (http >= 500) code = 'server'
    return { http, code, raw: input }
  }
  return { http: 0, code: 'unknown', raw: input }
}
