import {
  Badge,
  Box,
  Button,
  Heading,
  HStack,
  Icon,
  SimpleGrid,
  Text,
  VStack,
  Wrap,
  WrapItem,
} from '@chakra-ui/react'
import { Link as RouterLink, useParams } from 'react-router-dom'
import { FiFileText, FiFilm, FiImage, FiVideo } from 'react-icons/fi'
import sampleAnalysisResponse from '../data/sampleAnalysisResponse.json'

const mediaIconMap = {
  image: FiImage,
  video: FiVideo,
  gif: FiFilm,
}

const engagementColorMap = {
  high: 'green',
  medium: 'yellow',
  low: 'gray',
}

const capitalize = (value) => {
  if (!value || typeof value !== 'string') {
    return ''
  }

  return value.charAt(0).toUpperCase() + value.slice(1)
}

const AnalysisPage = () => {
  const { id } = useParams()
  const { suggested_posts: suggestedPosts = [] } = sampleAnalysisResponse

  const renderPredictedEngagementBadge = (level) => {
    const normalizedLevel = typeof level === 'string' ? level.toLowerCase() : ''
    const colorScheme = engagementColorMap[normalizedLevel] || 'gray'

    return (
      <Badge colorScheme={colorScheme} textTransform="capitalize" fontSize="sm">
        {normalizedLevel || 'Unknown'}
      </Badge>
    )
  }

  const renderMediaSuggestion = (media) => {
    const normalizedMedia = typeof media === 'string' ? media.toLowerCase() : ''
    const MediaIcon = mediaIconMap[normalizedMedia] || FiFileText

    return (
      <HStack spacing={2} color="gray.500">
        <Icon as={MediaIcon} boxSize={5} />
        <Text fontSize="sm" fontWeight="medium" textTransform="capitalize">
          {normalizedMedia || 'Not specified'}
        </Text>
      </HStack>
    )
  }

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
        <Box
          bg="white"
          borderRadius="3xl"
          boxShadow="lg"
          border="1px solid"
          borderColor="gray.100"
          px={{ base: 6, md: 8 }}
          py={{ base: 8, md: 10 }}
        >
          <VStack align="stretch" gap={6}>
            <VStack align="stretch" gap={3}>
              <Heading size="lg" color="gray.800">
                Suggested Posts
              </Heading>
              <Text color="gray.600">
                These ideas are tuned for high engagement. Review the copy, recommended media, and
                supporting rationale before scheduling.
              </Text>
            </VStack>
            {suggestedPosts.length > 0 ? (
              <SimpleGrid columns={{ base: 1, md: 2 }} gap={6}>
                {suggestedPosts.map((post, index) => {
                  const mediaLabel = capitalize(post?.media_suggestion) || 'Content'

                  return (
                    <Box
                      key={`${post.media_suggestion}-${index}`}
                      borderRadius="2xl"
                      border="1px solid"
                      borderColor="gray.100"
                      bg="gray.50"
                      _hover={{ borderColor: 'gray.200', boxShadow: 'md', bg: 'white' }}
                      transition="all 0.2s ease"
                      p={6}
                    >
                      <VStack align="stretch" gap={4}>
                        <HStack justify="space-between" align="flex-start">
                          <VStack align="flex-start" spacing={1}>
                            <Text fontSize="sm" color="gray.500">
                              Idea {index + 1}
                            </Text>
                            <Text fontWeight="semibold" color="gray.800">
                              {mediaLabel} focus
                            </Text>
                          </VStack>
                          {renderPredictedEngagementBadge(post.predicted_engagement)}
                        </HStack>

                        <Text fontSize="md" color="gray.700">
                          {post.text}
                        </Text>

                        {post.hashtags?.length > 0 && (
                          <Wrap spacing={2}>
                            {post.hashtags.map((tag) => (
                              <WrapItem key={`${tag}`}>
                                <Badge
                                  variant="subtle"
                                  colorPalette="blue"
                                  borderRadius="full"
                                  fontWeight="medium"
                                >
                                  {tag}
                                </Badge>
                              </WrapItem>
                            ))}
                          </Wrap>
                        )}

                        <Box borderTopWidth="1px" borderColor="gray.200" />

                        <VStack align="stretch" spacing={3}>
                          {renderMediaSuggestion(post.media_suggestion)}
                          {post.rationale && (
                            <Text fontSize="sm" color="gray.600" lineHeight="tall">
                              {post.rationale}
                            </Text>
                          )}
                        </VStack>
                      </VStack>
                    </Box>
                  )
                })}
              </SimpleGrid>
            ) : (
              <Box
                borderRadius="2xl"
                border="1px dashed"
                borderColor="gray.200"
                py={12}
                px={6}
                textAlign="center"
              >
                <Text fontWeight="medium" color="gray.700">
                  No suggested posts were generated for this analysis.
                </Text>
                <Text fontSize="sm" color="gray.500" mt={2}>
                  Run another analysis to see fresh ideas tailored to your audience.
                </Text>
              </Box>
            )}
          </VStack>
        </Box>
      </VStack>
    </Box>
  )
}

export default AnalysisPage
