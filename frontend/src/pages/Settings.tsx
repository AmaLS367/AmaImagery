import { motion } from 'framer-motion'
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card'
import { Label } from '../components/ui/label'
import { Switch } from '../components/ui/switch'
export default function Settings({ theme, toggleTheme }: { theme: 'light'|'dark', toggleTheme: () => void }) {
  return (
    <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -12 }} transition={{ duration: 0.35, ease: 'easeOut' }} className="container py-4">
      <Card><CardHeader><CardTitle>Настройки</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-1"><Label className="text-foreground">Тёмная тема</Label><div className="text-sm text-muted-foreground">Переключение оформления интерфейса</div></div>
            <Switch checked={theme === 'dark'} onCheckedChange={toggleTheme} />
          </div>
        </CardContent>
      </Card>
    </motion.div>
  )
}
