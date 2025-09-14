export type Template = { id: string; name: string; text: string }
export const DEFAULT_TEMPLATES: Template[] = [
  { id: 'portrait', name: 'Portrait', text: '${style} portrait of ${subject}, ultra-detailed, 8k, studio lighting' },
  { id: 'landscape', name: 'Landscape', text: '${style} landscape of ${subject}, dramatic sky, volumetric light, depth of field' },
  { id: 'product', name: 'Product Shot', text: '${subject} on seamless background, soft shadows, high key, editorial, ${style}' },
  { id: 'anime', name: 'Anime', text: 'anime style, ${subject}, crisp lineart, vibrant colors, detailed background' },
]
export type Vars = Record<string, string>
export function renderTemplate(t: string, vars: Vars): string {
  return t.replace(/\$\{(\w+)\}/g, (_, k) => (vars[k] ?? ''))
}
