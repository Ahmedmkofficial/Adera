import { useEffect, useMemo, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Controls, ReactFlow } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import '../components/admin/graph.css'
import { AccountNode, ReportNode, SubjectNode } from '../components/admin/GraphNodes'
import { SelectionContext } from '../components/admin/graphContext'
import { layoutGraph } from '../utils/graphLayout'
import { getGraph } from '../services/api'
import { formatDateTime, formatReportId } from '../utils/format'
import { levelClass, levelLabel } from '../utils/risk'

// Defined once, outside the component, so React Flow doesn't rebuild them on every render.
const nodeTypes = { subject: SubjectNode, account: AccountNode, report: ReportNode }

const KIND_LABEL = { subject: 'Recipient', account: 'Account', report: 'Report' }

// A new phone number in the address starts the page fresh (key = phone)
export default function GraphRoute() {
  const { phone } = useParams()
  return <GraphPage key={phone} phone={phone} />
}

function GraphPage({ phone }) {
  const [data, setData] = useState(undefined) // undefined = loading, null = not found
  const [error, setError] = useState('')

  useEffect(() => {
    let cancelled = false
    getGraph(phone)
      .then((result) => {
        if (!cancelled) setData(result)
      })
      .catch(() => {
        if (!cancelled) setError('Could not load the graph. Please refresh the page.')
      })
    return () => {
      cancelled = true
    }
  }, [phone])

  if (error) {
    return (
      <div className="op-page">
        <p className="op-error" role="alert">{error}</p>
      </div>
    )
  }
  if (data === undefined) {
    return (
      <div className="op-page">
        <p className="op-empty">Loading graph…</p>
      </div>
    )
  }
  if (data === null) {
    return (
      <div className="op-page">
        <h1 className="iv-notfound">No record found</h1>
        <p className="op-muted">
          Adera has no relationship data for {phone}. <Link to="/admin/entities">Back to entities</Link>
        </p>
      </div>
    )
  }
  return <GraphView data={data} />
}

function GraphView({ data }) {
  const subject = data.nodes.find((n) => n.kind === 'subject')
  const [selectedId, setSelectedId] = useState(subject.id)
  const { nodes, edges } = useMemo(() => layoutGraph(data), [data])

  const selected = data.nodes.find((n) => n.id === selectedId) ?? subject
  const accountCount = data.nodes.filter((n) => n.kind !== 'report').length
  const reportsShown = data.nodes.filter((n) => n.kind === 'report').length
  const relation = data.edges.find((e) => e.target === selected.id && e.type !== 'REPORT')?.type

  return (
    <div className="gr-page">
      <div className="gr-head">
        <div>
          <p className="op-eyebrow">RELATIONSHIP GRAPH</p>
          <h1>Connected entities</h1>
          <p className="gr-sub">
            {accountCount} {accountCount === 1 ? 'account' : 'accounts'} · showing {reportsShown} of{' '}
            {data.reports_total} reports
          </p>
        </div>
        <Link className="gr-back" to={`/admin/entity/${data.phone}`}>← Back to profile</Link>
      </div>

      <div className="gr-layout">
        <div className="gr-canvas">
          <SelectionContext.Provider value={selectedId}>
            <ReactFlow
              className="gr-flow"
              aria-label="Relationship graph"
              nodes={nodes}
              edges={edges}
              nodeTypes={nodeTypes}
              onNodeClick={(_, node) => setSelectedId(node.id)}
              nodesDraggable={false}
              nodesConnectable={false}
              nodesFocusable={false}
              edgesFocusable={false}
              fitView
              fitViewOptions={{ padding: 0.25 }}
              minZoom={0.4}
              maxZoom={1.6}
            >
              <Controls showInteractive={false} position="bottom-right" />
            </ReactFlow>
          </SelectionContext.Provider>

          <ul className="gr-legend" aria-label="Legend">
            <li><span className="gr-key gr-key-ring" />Recipient</li>
            <li><span className="gr-key gr-key-dot" />Account</li>
            <li><span className="gr-key gr-key-square" />Fraud report</li>
          </ul>
        </div>

        <aside className="gr-inspector" aria-label="Selected node details">
          <p className="op-eyebrow">SELECTED</p>

          {selected.kind === 'report' ? (
            <>
              <h2 className="mono">{formatReportId(selected.report_id)}</h2>
              <dl className="gr-facts">
                <div><dt>Type</dt><dd>Fraud report</dd></div>
                <div><dt>Category</dt><dd>{selected.scam_type}</dd></div>
                <div><dt>Reported</dt><dd>{formatDateTime(selected.created_at)}</dd></div>
              </dl>
              <p className="gr-summary">{selected.summary}</p>
            </>
          ) : (
            <>
              <h2>{selected.kind === 'subject' ? 'Recipient account' : 'Related account'}</h2>
              <p className="gr-phone mono">{selected.phone}</p>
              <dl className="gr-facts">
                <div>
                  <dt>Risk</dt>
                  <dd className={`gr-lvl ${levelClass(selected.level)}`}>
                    {levelLabel(selected.level)}
                    {selected.score != null ? ` · ${selected.score}` : ''}
                  </dd>
                </div>
                <div><dt>Reports</dt><dd>{selected.report_count}</dd></div>
                <div>
                  <dt>Last activity</dt>
                  <dd>{selected.last_activity ? formatDateTime(selected.last_activity) : '—'}</dd>
                </div>
                {relation && (
                  <div><dt>Connected by</dt><dd className="mono">{relation}</dd></div>
                )}
              </dl>
              <Link className="gr-open" to={`/admin/entity/${selected.phone}`}>Open profile →</Link>
            </>
          )}

          <div className="gr-nodes">
            <p className="op-eyebrow">ALL NODES</p>
            <ul>
              {data.nodes.map((n) => (
                <li key={n.id}>
                  <button
                    type="button"
                    className="mono"
                    aria-pressed={n.id === selectedId}
                    onClick={() => setSelectedId(n.id)}
                  >
                    {n.kind === 'report' ? formatReportId(n.report_id) : n.phone}
                  </button>
                  <span className="op-muted">{KIND_LABEL[n.kind]}</span>
                </li>
              ))}
            </ul>
          </div>
        </aside>
      </div>
    </div>
  )
}
