// Session state management — placeholder, stateful logic, no styling.
// See mobile/CLAUDE.md → Component Structure.

import { ReactNode } from 'react'

export type SessionContainerProps = {
  sessionId: string
  children?: ReactNode
}

export function SessionContainer(props: SessionContainerProps): JSX.Element {
  return <>{props.children}</>
}
