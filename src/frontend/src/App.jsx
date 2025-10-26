import { useState } from 'react'
import { Box, Center, Heading, Text, VStack } from '@chakra-ui/react'
import './App.css'
import LinkInput from './components/LinkInput'
import ShimmerText from './components/ui/shimmerText/ShimmerText'
import { RiExpandRightLine } from "react-icons/ri";
import StatusBanner from './components/StatusBanner'

function App() {
  const [status, setStatus] = useState('idle') // 'idle' | 'processing' | 'success' | 'error'
  const [errorMsg, setErrorMsg] = useState('')
  const [resultId, setResultId] = useState(null)

  const handleAnalyze = async (link) => {
    console.log('Analyzing link:', link)
    setStatus('processing')
    setErrorMsg('')

    try {
      // TODO: wire up the real analysis call here
      // Example: const { id } = await analyzeLink(link)
      // setResultId(id)
      // setStatus('success')

      // Temporary demo success to show UI
      setTimeout(() => {
        setResultId('demo-id')
        setStatus('success')
      }, 1000)
    } catch (e) {
      console.error(e)
      setErrorMsg(e?.message || 'Something went wrong. Please try again.')
      setStatus('error')
    } finally {
      // no-op; status managed above
    }
  }

  const handleViewResults = () => {
    // TODO: navigate to a results route/page
    // e.g., navigate(`/results/${resultId}`)
    console.log('Go to results:', resultId)
  }
  
  return (
    <Box minH="100vh" bg="gray.50">
      <Center minH="100vh" px={{ base: 6, md: 12 }}>
        <VStack
          gap={12}
          align="stretch"
          maxW="4xl"
          w="full"
          textAlign="center"
        >
          <VStack gap={3}>
            <Heading size="5xl" fontWeight="semibold" color="var(--brand-primary)">
              Ready to uncover insights?
            </Heading>
            <Text fontSize="lg" color="gray.500">
              Paste a social profile link to get an AI-powered analysis and next-step recommendations.
            </Text>
          </VStack>

          <Box
            bg="white"
            borderRadius="3xl"
            boxShadow="xl"
            px={{ base: 6, md: 10 }}
            py={{ base: 8, md: 10 }}
            border="1px solid"
            borderColor="gray.100"
          >
            <VStack gap={6} align="stretch">
              <Text fontSize="md" color="gray.600" textAlign="left">
                Enter profile URL to start your analysis
              </Text>
              <LinkInput onAnalyze={handleAnalyze} isDisabled={status === 'processing'} />
            </VStack>
            {status === 'processing' && (
              <Box mt={2} textAlign="left">
                <Box as="span" display="inline-flex" alignItems="baseline" gap={1} lineHeight={2} cursor="pointer">
                  <ShimmerText>Analyzing</ShimmerText>
                  <Box as={RiExpandRightLine} boxSize={4} transform="translateY(3px)" color="#999" />
                </Box>
              </Box>
            )}
            {status === 'success' && (
              <StatusBanner
                type="success"
                title="Analysis complete"
                message="Your insights are ready."
                actionLabel="View results"
                onAction={handleViewResults}
                onClose={() => setStatus('idle')}
              />
            )}
            {status === 'error' && (
              <StatusBanner
                type="error"
                title="Analysis failed"
                message={errorMsg || 'Something went wrong. Please try again.'}
                actionLabel="Retry"
                onAction={() => setStatus('idle')}
                onClose={() => setStatus('idle')}
              />
            )}
          </Box>
        </VStack>
      </Center>
    </Box>
  )
}

export default App
