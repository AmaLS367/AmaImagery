const WORDS = ['nsfw','18+','nude','nudity','explicit','porn','sex','boobs','naked','nsfw:1','erotic']

export function guessNSFW(prompt: string, negative: string | null | undefined): boolean {
  const s = (prompt + ' ' + (negative || '')).toLowerCase()
  return WORDS.some(w => s.includes(w))
}
