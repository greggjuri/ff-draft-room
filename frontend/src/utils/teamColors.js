const TEAM_COLORS = {
  ARI: '#97233F', ATL: '#A71930', BAL: '#241773', BUF: '#C60C30',
  CAR: '#0085CA', CHI: '#C83803', CIN: '#FB4F14', CLE: '#FF3C00',
  DAL: '#00338D', DEN: '#FB4F14', DET: '#0076B6', GB:  '#FFB612',
  HOU: '#A71930', IND: '#002C5F', JAC: '#006778', KC:  '#E31837',
  LV:  '#A5ACAF', LAC: '#0073CF', LAR: '#B3995D', MIA: '#008E97',
  MIN: '#4F2683', NE:  '#C60C30', NO:  '#D3BC8D', NYG: '#A71930',
  NYJ: '#003F2D', PHI: '#004C54', PIT: '#FFB612', SF:  '#AA0000',
  SEA: '#69BE28', TB:  '#D50A0A', TEN: '#4B92DB', WSH: '#773141',
}

const FREE_AGENT_TOKENS = new Set(['FA', '--', '', 'FA '])

export function getTeamColor(team) {
  if (!team || FREE_AGENT_TOKENS.has(team.trim())) return null
  return TEAM_COLORS[team.toUpperCase()] ?? null
}
