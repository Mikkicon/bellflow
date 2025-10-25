import { Box, Center, Heading, Text, VStack } from '@chakra-ui/react'
import './App.css'
import LinkInput from './components/LinkInput'

function App() {
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
              <LinkInput />
            </VStack>
          </Box>
        </VStack>
      </Center>
    </Box>
  )
}

export default App
