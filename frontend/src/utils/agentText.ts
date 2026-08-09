/** Strip common LaTeX fragments agents sometimes emit in summaries. */
export function sanitizeAgentText(text: string): string {
  if (!text) return text
  let out = text.replace(/\$([^$]+)\$/g, (_m, inner: string) => latexChunkToPlain(inner))
  out = out.replace(/\\(?:text|mathrm|textrm|mathbf)\{([^}]*)\}/g, '$1')
  out = out.replace(/\\circ/g, '°')
  out = out.replace(/\^\s*°/g, '°')
  out = out.replace(/\^\s*C\b/g, ' C')
  return out
}

function latexChunkToPlain(inner: string): string {
  let plain = inner
  plain = plain.replace(/\\circ/g, '°')
  plain = plain.replace(/\\times/g, 'x')
  plain = plain.replace(/\\[,; ]/g, ' ')
  plain = plain.replace(/\\(?:text|mathrm|textrm|mathbf)\{([^}]*)\}/g, '$1')
  plain = plain.replace(/[{}]/g, '')
  plain = plain.replace(/\\/g, '')
  plain = plain.replace(/\^\s*°/g, '°')
  plain = plain.replace(/\^\s*C\b/g, ' C')
  return plain.replace(/\s+/g, ' ').trim()
}

/** Pull a short Reasoning paragraph from an agent summary. */
export function extractReasoning(summary?: string | null): string | null {
  if (!summary) return null
  const cleaned = sanitizeAgentText(summary)
  const match = cleaned.match(
    /(?:\*\*)?reasoning(?:\*\*)?\s*[:\-–]\s*([\s\S]+?)(?=\n\s*(?:#{1,4}\s|\*\*[A-Z]|\d+\.\s+[A-Z]|Actions?\s+Taken|$))/i,
  )
  if (!match) return null
  const text = match[1].replace(/\s+/g, ' ').replace(/^[-* ]+/, '').trim()
  return text.length >= 8 ? text.slice(0, 500) : null
}
