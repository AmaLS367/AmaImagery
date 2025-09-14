import { Input } from './ui/input'
import { Label } from './ui/label'

export type Filters = {
  q: string
  ratio: 'any'|'1:1'|'3:4'|'4:3'|'9:16'|'16:9'
  cfg: 'any'| 'lt6' | '6-8' | 'gt8'
  onlyPinned: boolean
  hideNSFW: boolean
}

export function HistoryFilters({ value, onChange }: { value: Filters, onChange: (v: Filters)=>void }) {
  return (
    <div className="flex flex-wrap items-center gap-3 rounded-md border p-3">
      <div className="flex-1 min-w-[220px]">
        <Input placeholder="Поиск по промпту/тегам…" value={value.q} onChange={e=>onChange({ ...value, q: e.target.value })} />
      </div>
      <div className="flex items-center gap-2">
        <Label>ratio</Label>
        <select className="rounded-md border bg-background p-2 text-sm" value={value.ratio} onChange={e=>onChange({ ...value, ratio: e.target.value as any })}>
          {['any','1:1','3:4','4:3','9:16','16:9'].map(x=> <option key={x} value={x}>{x}</option>)}
        </select>
      </div>
      <div className="flex items-center gap-2">
        <Label>CFG</Label>
        <select className="rounded-md border bg-background p-2 text-sm" value={value.cfg} onChange={e=>onChange({ ...value, cfg: e.target.value as any })}>
          <option value="any">any</option>
          <option value="lt6">&lt;6</option>
          <option value="6-8">6..8</option>
          <option value="gt8">&gt;8</option>
        </select>
      </div>
      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" className="accent-primary" checked={value.onlyPinned} onChange={e=>onChange({ ...value, onlyPinned: e.target.checked })}/>
        только pinned
      </label>
      <label className="flex items-center gap-2 text-sm">
        <input type="checkbox" className="accent-primary" checked={value.hideNSFW} onChange={e=>onChange({ ...value, hideNSFW: e.target.checked })}/>
        скрывать NSFW
      </label>
    </div>
  )
}
