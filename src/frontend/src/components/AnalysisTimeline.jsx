import { Timeline, Text } from '@chakra-ui/react'
import { LuPackage, LuCheck } from 'react-icons/lu'

const taskIcon = <LuPackage />
const eventIcon = <LuCheck />

const formatTimestamp = (isoString) => {
  if (!isoString) return null

  try {
    const date = new Date(isoString)
    return date.toLocaleString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch (e) {
    console.warn('Failed to parse timestamp', isoString, e)
    return isoString
  }
}

const AnalysisTimeline = ({ items = [], ...props }) => {
  const timelineEntries = []

  items.forEach((item) => {
    timelineEntries.push({
      key: item.id,
      kind: 'task',
      title: item.name,
      description: formatTimestamp(item.timestamp),
      message: item.message,
      status: item.status,
    })

    item.events?.forEach((event) => {
      timelineEntries.push({
        key: `${item.id}-${event.id}`,
        kind: 'event',
        title: event.name,
        description: formatTimestamp(event.timestamp),
        message: event.message,
        status: event.status,
      })
    })
  })

  return (
    <Timeline.Root {...props}>
      {timelineEntries.map((entry) => (
        <Timeline.Item key={entry.key}>
          <Timeline.Connector>
            <Timeline.Separator />
            <Timeline.Indicator color={entry.kind === 'task' ? 'blue.500' : 'green.500'}>
              {entry.kind === 'task' ? taskIcon : eventIcon}
            </Timeline.Indicator>
          </Timeline.Connector>
          <Timeline.Content>
            <Timeline.Title>{entry.title}</Timeline.Title>
            {entry.description && (
              <Timeline.Description>{entry.description}</Timeline.Description>
            )}
            {/* {entry.status && (
              <Text textStyle="sm" color="gray.500">
                Status: <strong>{entry.status}</strong>
              </Text>
            )} */}
            {entry.message && (
              <Text textStyle="sm" color="gray.600">
                {entry.message}
              </Text>
            )}
          </Timeline.Content>
        </Timeline.Item>
      ))}
    </Timeline.Root>
  )
}

export default AnalysisTimeline
