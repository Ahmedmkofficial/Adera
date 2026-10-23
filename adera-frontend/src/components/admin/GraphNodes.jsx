import { useContext } from 'react'
import { Handle, Position } from '@xyflow/react'
import { CENTER_Y } from '../../utils/graphLayout'
import { formatReportId } from '../../utils/format'
import { levelClass } from '../../utils/risk'
import { SelectionContext } from './graphContext'

// Invisible 2px connection points placed at the CENTER of each node's shape,
// so lines run from circle center to circle center.
function Handles({ y }) {
  const style = { opacity: 0, width: 2, height: 2, minWidth: 2, minHeight: 2, top: y, left: '50%' }
  return (
    <>
      <Handle type="target" position={Position.Top} isConnectable={false} style={style} />
      <Handle type="source" position={Position.Top} isConnectable={false} style={style} />
    </>
  )
}

export function SubjectNode({ id, data }) {
  const selected = useContext(SelectionContext) === id
  return (
    <div className={`gr-node gr-subject ${levelClass(data.level)}${selected ? ' is-selected' : ''}`}>
      <Handles y={CENTER_Y.subject} />
      <span className="gr-name">Recipient</span>
      <span className="gr-meta">{data.phone}</span>
      <span className="gr-ring"><span className="gr-core" /></span>
    </div>
  )
}

export function AccountNode({ id, data }) {
  const selected = useContext(SelectionContext) === id
  return (
    <div className={`gr-node ${levelClass(data.level)}${selected ? ' is-selected' : ''}`}>
      <Handles y={CENTER_Y.account} />
      <span className="gr-dot" />
      <span className="gr-name">Account</span>
      <span className="gr-meta">{data.phone}</span>
    </div>
  )
}

export function ReportNode({ id, data }) {
  const selected = useContext(SelectionContext) === id
  return (
    <div className={`gr-node${selected ? ' is-selected' : ''}`}>
      <Handles y={CENTER_Y.report} />
      <span className="gr-square" />
      <span className="gr-name">{formatReportId(data.report_id)}</span>
      <span className="gr-meta">{data.scam_type}</span>
    </div>
  )
}