import { useMemo, useRef } from 'react'
import { Timeline, Text } from '@chakra-ui/react'
import { AnimatePresence, motion } from 'framer-motion'
import { LuPackage, LuCheck } from 'react-icons/lu'

const MotionTimelineItem = motion(Timeline.Item)

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
  const seenEntryIdsRef = useRef(new Set())

  const timelineEntries = useMemo(() => {
    if (items.length === 0) {
      seenEntryIdsRef.current.clear()
      return []
    }

    const entries = []

    items.forEach((item) => {
      entries.push({
        key: item.id,
        kind: 'task',
        title: item.name,
        description: formatTimestamp(item.timestamp),
        message: item.message,
        status: item.status,
      })

      item.events?.forEach((event) => {
        entries.push({
          key: `${item.id}-${event.id}`,
          kind: 'event',
          title: event.name,
          description: formatTimestamp(event.timestamp),
          message: event.message,
          status: event.status,
        })
      })
    })

    return entries.map((entry) => {
      const isNew = !seenEntryIdsRef.current.has(entry.key)

      if (isNew) {
        seenEntryIdsRef.current.add(entry.key)
      }

      return { ...entry, isNew }
    })
  }, [items])

  return (
    <Timeline.Root {...props}>
      <AnimatePresence initial={false}>
        {timelineEntries.map((entry) => (
          <MotionTimelineItem
            key={entry.key}
            initial={entry.isNew ? { opacity: 0, y: 12 } : false}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -12 }}
            transition={{ duration: 0.25, ease: 'easeOut' }}
            layout
          >
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
                <Text textStyle="sm" color="gray.500" mt={entry.message ? 1 : 0}>
                  Status: <Text as="span" fontWeight="semibold">{entry.status}</Text>
                </Text>
              )} */}
              {entry.message && (
                <Text textStyle="sm" color="gray.600">
                  {entry.message}
                </Text>
              )}
            </Timeline.Content>
          </MotionTimelineItem>
        ))}
      </AnimatePresence>
    </Timeline.Root>
  )
}

export default AnalysisTimeline
