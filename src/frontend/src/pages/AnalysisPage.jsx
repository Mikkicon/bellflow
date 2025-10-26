import { Box, Button, Heading, Text, VStack } from '@chakra-ui/react'
import { Link as RouterLink, useParams } from 'react-router-dom'
import AnalysisTimeline from '../components/AnalysisTimeline'
import { demoTimelineData } from '../data/demoTimelineData'

const AnalysisPage = () => {
  const { id } = useParams()

  return (
    <Box minH="100vh" bg="gray.50" py={16} px={{ base: 6, md: 12 }}>
      <VStack gap={8} align="stretch" maxW="5xl" mx="auto">
        <Heading size="4xl" color="var(--brand-primary)">
          Analysis summary
        </Heading>
        <Text color="gray.600" fontSize="lg">
          Displaying generated insights for request{' '}
          <Text as="span" fontWeight="semibold">{id}</Text>.
        </Text>
        <Button as={RouterLink} to="/" alignSelf="flex-start" size="sm">
          Run another analysis
        </Button>
      </VStack>
    </Box>
  )
}

export default AnalysisPage
