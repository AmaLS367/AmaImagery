import { EditorialFrame } from '../components/editorial/EditorialFrame'
import { SurfacePanel } from '../components/ui/foundation'

const templates = [
  {
    title: 'Prompt formula',
    code: 'Subject + scene + composition + lighting + finish + constraints',
    detail: 'Keep the prompt legible. A short, explicit structure usually performs better than a paragraph of loosely related descriptors.',
  },
  {
    title: 'Portrait starter',
    code: 'Editorial portrait, confident subject, waist-up crop, clean eye detail, soft key light, subtle rim, premium finish',
    detail: 'Use this when the output needs polish without heavy environmental storytelling.',
  },
  {
    title: 'Environment starter',
    code: 'Product interior, controlled palette, wide framing, structured reflections, cinematic but readable lighting',
    detail: 'Good for scene-building when you still need the subject and composition to stay anchored.',
  },
]

const doList = [
  'Name the subject before describing mood.',
  'Set lighting and framing explicitly when they matter.',
  'Use the negative prompt to remove distortions or clutter.',
  'Save successful outputs and reuse their settings from history.',
]

const dontList = [
  'Do not bury the main subject under stylistic filler.',
  'Do not combine incompatible camera, pose, and scene directions in one line.',
  'Do not raise CFG and size together without a reason.',
  'Do not hide recovery instructions inside the prompt itself.',
]

export default function PromptGuide() {
  return (
    <EditorialFrame
      eyebrow="Prompt Guide"
      title="Write prompts that stay readable for both the model and the operator."
      summary="This guide keeps the structure practical: prompt formula, strong starting templates, correction habits, and the small mistakes that usually hurt output quality."
      pills={['Formula first', 'Correction-aware', 'Runtime-friendly']}
    >
      <div className="grid gap-6 xl:grid-cols-[1.05fr_0.95fr]">
        <SurfacePanel className="space-y-5 p-6 md:p-8">
          <div className="space-y-3">
            <h2 className="font-display text-[28px] font-semibold tracking-[-0.05em]">Quick rules</h2>
            <p className="text-sm leading-6 text-muted-foreground">
              The generator works best when the prompt is explicit, the scene is constrained, and the negative guidance
              removes likely failures instead of repeating the same mood words.
            </p>
          </div>
          <div className="grid gap-4">
            {templates.map((template) => (
              <SurfacePanel key={template.title} className="rounded-[24px] p-5 shadow-none">
                <div className="font-display text-2xl font-semibold tracking-[-0.05em] text-foreground">{template.title}</div>
                <pre className="mt-3 overflow-x-auto rounded-[18px] bg-background/60 p-4 text-sm text-foreground">{template.code}</pre>
                <p className="mt-3 text-sm leading-6 text-muted-foreground">{template.detail}</p>
              </SurfacePanel>
            ))}
          </div>
        </SurfacePanel>

        <div className="space-y-6">
          <SurfacePanel className="space-y-4 p-6">
            <h2 className="font-display text-[28px] font-semibold tracking-[-0.05em]">Do</h2>
            <ul className="space-y-3 text-sm leading-6 text-muted-foreground">
              {doList.map((item) => (
                <li key={item} className="rounded-[20px] border border-border/60 bg-card/60 px-4 py-3">
                  {item}
                </li>
              ))}
            </ul>
          </SurfacePanel>

          <SurfacePanel className="space-y-4 p-6">
            <h2 className="font-display text-[28px] font-semibold tracking-[-0.05em]">Do not</h2>
            <ul className="space-y-3 text-sm leading-6 text-muted-foreground">
              {dontList.map((item) => (
                <li key={item} className="rounded-[20px] border border-border/60 bg-card/60 px-4 py-3">
                  {item}
                </li>
              ))}
            </ul>
          </SurfacePanel>

          <SurfacePanel className="space-y-4 p-6">
            <h2 className="font-display text-[28px] font-semibold tracking-[-0.05em]">Correction habit</h2>
            <p className="text-sm leading-6 text-muted-foreground">
              When a result misses the mark, change one variable at a time. Keep the seed when you want a fair comparison,
              and use history to compare prompts, ratio, CFG, and steps instead of editing blindly.
            </p>
          </SurfacePanel>
        </div>
      </div>
    </EditorialFrame>
  )
}
