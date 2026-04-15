const OVERRIDES = {
  JAC: 'jax',
}

const FREE_AGENT_TOKENS = new Set(['FA', '--', '', 'FA '])

export function getLogoUrl(team) {
  if (!team || FREE_AGENT_TOKENS.has(team.trim())) return null
  const abbrev = OVERRIDES[team.toUpperCase()] ?? team.toLowerCase()
  return `https://a.espncdn.com/i/teamlogos/nfl/500/${abbrev}.png`
}
