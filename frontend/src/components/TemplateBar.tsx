import { DEFAULT_TEMPLATES, renderTemplate } from '../lib/templates'
import { Button } from './ui/button'
import { Input } from './ui/input'
import { useState } from 'react'

export function TemplateBar({ onInsert }: { onInsert: (text: string) => void }) {
  const [style, setStyle] = useState('cinematic')
  const [subject, setSubject] = useState('a girl with red umbrella')
  return (
    <div className="flex flex-wrap items-end gap-2 rounded-md border p-2">
      <div className="flex w-full flex-wrap items-end gap-2 sm:w-auto">
        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted-foreground">style</label>
          <Input value={style} onChange={e=>setStyle(e.target.value)} placeholder="cinematic" className="w-40"/>
        </div>
        <div className="flex flex-col gap-1">
          <label className="text-xs text-muted-foreground">subject</label>
          <Input value={subject} onChange={e=>setSubject(e.target.value)} placeholder="subject" className="min-w-[220px]"/>
        </div>
      </div>
      <div className="flex flex-wrap gap-2">
        {DEFAULT_TEMPLATES.map(t => (
          <Button key={t.id} variant="outline" onClick={()=>onInsert(renderTemplate(t.text, { style, subject }))}>
            {t.name}
          </Button>
        ))}
      </div>
    </div>
  )
}
