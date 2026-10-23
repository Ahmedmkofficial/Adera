// Height of the shape at the top of each node, halved. These numbers must match
// the sizes in graph.css: subject label block 40px + ring 40px (center 60),
// account dot 16px (center 8), report square 10px (center 5).
export const NODE_W = 150
export const CENTER_Y = { subject: 60, account: 8, report: 5 }

// evenly spaced offsets around 0: spread(3, 100) -> [-100, 0, 100]
const spread = (n, step) => Array.from({ length: n }, (_, i) => (i - (n - 1) / 2) * step)

// Accounts go left and right of the recipient, on the same line, so the labels
// under their circles never sit on top of a connecting line.
function accountSpot(i) {
  const side = i % 2 === 0 ? 1 : -1
  const ring = Math.floor(i / 2) + 1
  return [side * 340 * ring, (ring - 1) * 130]
}

export function layoutGraph(data) {
  const subject = data.nodes.find((n) => n.kind === 'subject')
  const accounts = data.nodes.filter((n) => n.kind === 'account')
  const reports = data.nodes.filter((n) => n.kind === 'report')
  const reportXs = spread(reports.length, 200)

  // (cx, cy) is where the CENTER of the shape should sit
  const place = (node, cx, cy) => ({
    id: node.id,
    type: node.kind,
    position: { x: cx - NODE_W / 2, y: cy - CENTER_Y[node.kind] },
    data: node,
  })

  const nodes = [
    place(subject, 0, 0),
    ...accounts.map((n, i) => place(n, ...accountSpot(i))),
    ...reports.map((n, i) => place(n, reportXs[i], 190)),
  ]

  const edges = data.edges.map((e) => ({
    id: e.id,
    source: e.source,
    target: e.target,
    type: 'straight',
    label: e.type === 'REPORT' ? undefined : e.type,
    labelStyle: { fontFamily: '"JetBrains Mono", ui-monospace, monospace', fontSize: 11, fill: 'var(--muted)' },
    labelBgStyle: { fill: 'var(--paper)' },
    labelBgPadding: [6, 4],
  }))

  return { nodes, edges }
}