import { useEffect, useState } from 'react'
import { motion } from 'framer-motion'
import { Card, CardContent } from '../components/ui/card'
import { getHistory, type HistoryItem } from '../lib/storage'
export default function History() {
  const [items, setItems] = useState<HistoryItem[]>([])
  useEffect(() => { setItems(getHistory()) }, [])
  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12 }} transition={{ duration: 0.35, ease: 'easeOut' }} className="container py-4">
      {items.length === 0 ? <div className="grid min-h-[40vh] place-items-center text-sm text-muted-foreground">История пуста.</div> :
        <div className="grid gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
          {items.map((it, idx) => (
            <Card key={idx} className="overflow-hidden">
              <CardContent className="p-0">
                <a href={`/file?path=${encodeURIComponent(it.path)}`} target="_blank" rel="noreferrer">
                  <img src={`/file?path=${encodeURIComponent(it.path)}`} alt="" className="h-56 w-full object-cover" />
                </a>
                <div className="p-3 text-sm text-muted-foreground line-clamp-3">{it.prompt}</div>
              </CardContent>
            </Card>
          ))}
        </div>}
    </motion.div>
  )
}
