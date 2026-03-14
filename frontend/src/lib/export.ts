import JSZip from 'jszip'
import { saveAs } from 'file-saver'
import { toAssetUrl } from './api'
import type { HistoryItem } from './storage'

export async function exportHistoryZip(items: HistoryItem[]) {
  const zip = new JSZip()
  zip.file('metadata.json', JSON.stringify({ version: 1, items }, null, 2))
  const thumbs = zip.folder('thumbs')
  let idx = 0
  for (const it of items.slice(0, 100)) {
    try {
      const name = String(it.path || '').split(/[\\/]/).pop() || ''
      if (!name) continue

      const query = new URLSearchParams({ path: name })
      if (typeof it.exp === 'number') {
        query.set('exp', String(it.exp))
      }
      if (typeof it.sig === 'string' && it.sig.length > 0) {
        query.set('sig', it.sig)
      }

      const url = toAssetUrl(`/api/v1/file?${query.toString()}`)
      if (!url) continue

      const resp = await fetch(url, { credentials: 'include' })
      if (!resp.ok) continue
      const blob = await resp.blob()
      thumbs?.file(`${idx++}.png`, blob)
    } catch {}
  }
  const blobZip = await zip.generateAsync({ type: 'blob' })
  saveAs(blobZip, 'amaimagery-history.zip')
}

export async function importHistoryZip(file: File): Promise<{ items: HistoryItem[] }> {
  const zip = await JSZip.loadAsync(file)
  const meta = zip.file('metadata.json')
  if (!meta) throw new Error('metadata.json not found')
  const txt = await meta.async('text')
  const json = JSON.parse(txt)
  if (!Array.isArray(json.items)) throw new Error('bad metadata')
  return { items: json.items as HistoryItem[] }
}
