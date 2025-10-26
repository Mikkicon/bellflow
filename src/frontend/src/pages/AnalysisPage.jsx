import {
  Alert,
  Badge,
  Box,
  Button,
  Heading,
  HStack,
  Icon,
  Spinner,
  Text,
  VStack,
  Wrap,
  WrapItem,
  Flex,
  Card,
  CardBody,
  CardHeader,
  Separator,
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
  SimpleGrid,
} from '@chakra-ui/react'
import { Link as RouterLink, useParams } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { FiFileText, FiFilm, FiImage, FiVideo, FiChevronDown, FiHeart, FiMessageCircle, FiRepeat } from 'react-icons/fi'
import { fetchAnalysisById } from '../services/analysisService'

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

const getEngagementLevel = (post = {}) => {
  if (!post || typeof post !== 'object') {
    return null
  }

  if (post.predicted_engagement) {
    return post.predicted_engagement
  }

  const likes = post.estimated_likes ?? post.predicted_likes
  if (typeof likes !== 'number') {
    return null
  }

  if (likes >= 250) {
    return 'high'
  }

  if (likes >= 100) {
    return 'medium'
  }

  return 'low'
}

const AnalysisPage = () => {
  const { id } = useParams()
  const [analysisData, setAnalysisData] = useState(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(null)
  const [expandedCards, setExpandedCards] = useState({})
  const suggestedPosts = analysisData?.suggested_posts ?? []

  useEffect(() => {
    if (!id) {
      setAnalysisData(null)
      setIsLoading(false)
      return
    }

    let isActive = true

    const loadAnalysis = async () => {
      setIsLoading(true)
      setError(null)

      try {
        const response = await fetchAnalysisById(id)
        if (!isActive) {
          return
        }

        const analysis = response?.analysis ?? response ?? null
        setAnalysisData(analysis)
        setExpandedCards({})
      } catch (err) {
        if (!isActive) {
          return
        }

        const message = err?.message || 'Failed to load the requested analysis.'
        setError(message)
        setAnalysisData(null)
      } finally {
        if (isActive) {
          setIsLoading(false)
        }
      }
    }

    loadAnalysis()

    return () => {
      isActive = false
    }
  }, [id])

  const toggleCard = (index) => {
    setExpandedCards(prev => ({
      ...prev,
      [index]: !prev[index]
    }))
  }

  const generateRecentNews = () => {
    return [
      {
        id: 1,
        title: "AI Breakthrough in Natural Language Processing",
        source: "TechCrunch",
        timeAgo: "2h",
        category: "Technology"
      },
      {
        id: 2,
        title: "New Social Media Trends Emerging in 2024",
        source: "Social Media Today",
        timeAgo: "4h",
        category: "Social Media"
      },
      {
        id: 3,
        title: "Digital Marketing Strategies That Actually Work",
        source: "Marketing Land",
        timeAgo: "6h",
        category: "Marketing"
      },
      {
        id: 4,
        title: "Content Creation Tips for Higher Engagement",
        source: "Content Marketing Institute",
        timeAgo: "8h",
        category: "Content"
      },
      {
        id: 5,
        title: "The Future of Influencer Marketing",
        source: "Influencer Marketing Hub",
        timeAgo: "12h",
        category: "Influencer"
      },
      {
        id: 6,
        title: "Brand Storytelling in the Digital Age",
        source: "Brand Storytelling",
        timeAgo: "1d",
        category: "Branding"
      }
    ]
  }

  const formatCount = (count) => {
    if (count == null || Number.isNaN(count)) {
      return '--'
    }

    if (count >= 1000) {
      const formatted = (count / 1000).toFixed(1).replace(/\.0$/, '')
      return `${formatted}k`
    }

    return count.toString()
  }

  const renderPredictedEngagementBadge = (level) => {
    const normalizedLevel = typeof level === 'string' ? level.toLowerCase() : ''
    const colorScheme = engagementColorMap[normalizedLevel] || 'gray'

    return (
      <Badge colorScheme={colorScheme} textTransform="capitalize" fontSize="xs" px={2} py={1}>
        {normalizedLevel || 'Unknown'}
      </Badge>
    )
  }

  const renderMediaSuggestion = (post) => {
    const mediaHint = post?.media_suggestion || post?.media_type || ''
    const normalizedMedia = typeof mediaHint === 'string' ? mediaHint.toLowerCase() : ''
    const MediaIcon = mediaIconMap[normalizedMedia] || FiFileText
    const metrics = {
      likes: post?.estimated_likes ?? post?.predicted_likes,
      comments: post?.estimated_comments ?? post?.predicted_comments,
      reposts: post?.estimated_reposts ?? post?.predicted_reposts,
    }

    return (
      <VStack align="stretch" spacing={2}>
        <HStack spacing={1.5} color="gray.500">
          <Icon as={MediaIcon} boxSize={4} />
          <Text fontSize="xs" fontWeight="medium" textTransform="capitalize">
            {capitalize(mediaHint) || 'Content'}
          </Text>
        </HStack>

        {/* {post?.media_description && (
          <Text fontSize="xs" color="gray.600">
            {post.media_description}
          </Text>
        )} */}

        <HStack spacing={4} justify="space-between">
          <HStack spacing={1} color="gray.500">
            <Icon as={FiHeart} boxSize={3} />
            <Text fontSize="xs" fontWeight="medium">
              {formatCount(metrics.likes)}
            </Text>
          </HStack>

          <HStack spacing={1} color="gray.500">
            <Icon as={FiMessageCircle} boxSize={3} />
            <Text fontSize="xs" fontWeight="medium">
              {formatCount(metrics.comments)}
            </Text>
          </HStack>

          <HStack spacing={1} color="gray.500">
            <Icon as={FiRepeat} boxSize={3} />
            <Text fontSize="xs" fontWeight="medium">
              {formatCount(metrics.reposts)}
            </Text>
          </HStack>
        </HStack>
      </VStack>
    )
  }

  return (
    <Box
      minH="100vh"
      style={{
        background: 'linear-gradient(135deg, #bfdbfe 0%, #fbcfe8 50%, #c7d2fe 100%)',
        backgroundAttachment: 'fixed'
      }}
    >
      {/* Header Section - Left Aligned, Compact */}
      <Box py={8} px={{ base: 6, md: 12 }}>
        <HStack justify="space-between" align="flex-start" w="full">
           <VStack align="flex-start" gap={3}>
             <HStack spacing={3} align="center">
               <Heading size="2xl" color="var(--brand-primary)">
                 Analysis summary
               </Heading>
               <Text fontSize="2xl" filter="drop-shadow(0 0 4px rgba(255, 193, 7, 0.5))">
                 ✨
               </Text>
             </HStack>
            <Text color="gray.600" fontSize="md">
              Insights for request{' '}
              <Text as="span" fontWeight="semibold">{id}</Text>
            </Text>
          </VStack>
          <Button
            as={RouterLink}
            to="/"
            size="sm"
            bg="black"
            color="white"
            _hover={{ bg: "gray.800" }}
            _active={{ bg: "gray.900" }}
          >
            Run another analysis
          </Button>
        </HStack>
      </Box>

      {/* Ideas Section - Full Width */}
      <Box
        bg="white"
        bgOpacity={0.95}
        backdropFilter="blur(10px)"
        borderTop="1px solid"
        borderBottom="1px solid"
        borderColor="gray.200"
        px={{ base: 6, md: 12 }}
        py={{ base: 8, md: 12 }}
        boxShadow="0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)"
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
          {isLoading ? (
            <HStack spacing={3} color="gray.600">
              <Spinner size="sm" thickness="2px" speed="0.65s" />
              <Text fontSize="sm" fontWeight="medium">
                Loading analysis insights...
              </Text>
            </HStack>
          ) : error ? (
            <Alert.Root status="error" variant="subtle" borderRadius="md" alignItems="center">
              <Alert.Indicator />
              <Alert.Content>
                <Alert.Description fontSize="sm">
                  {error}
                </Alert.Description>
              </Alert.Content>
            </Alert.Root>
          ) : suggestedPosts.length > 0 ? (
            <Box w="full">
              <Flex
                direction={{ base: 'column', lg: 'row' }}
                gap={6}
                align="flex-start"
                justify="space-between"
                w="full"
                overflowX={{ base: 'visible', lg: 'auto' }}
                pb={2}
              >
                {suggestedPosts.map((post, index) => {
                  const engagementLevel = getEngagementLevel(post)
                  const postKey = post?.id || post?.media_suggestion || post?.media_type || post?.text || index
                  const mediaLabel = capitalize(post?.media_suggestion || post?.media_type) || 'Content'

                  return (
                    <Card.Root
                      key={postKey}
                      size="sm"
                      variant="outline"
                      minW={{ base: '100%', lg: '300px' }}
                      maxW={{ base: '100%', lg: '400px' }}
                      flex="1"
                      w="full"
                      boxShadow="0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1)"
                      _hover={{
                        borderColor: 'gray.300',
                        boxShadow: '0 20px 40px -10px rgba(0, 0, 0, 0.15), 0 12px 20px -8px rgba(0, 0, 0, 0.1)',
                        transform: 'translateY(-4px)'
                      }}
                      transition="all 0.3s ease"
                    >
                      <CardHeader pb={3}>
                        <VStack align="stretch" gap={3}>
                          <HStack justify="space-between" align="flex-start">
                            <VStack align="flex-start" spacing={1}>
                              <Text fontSize="xs" color="gray.500" fontWeight="medium">
                                IDEA {index + 1}
                              </Text>
                              <Text fontWeight="bold" color="gray.800" fontSize="sm">
                                {mediaLabel} Focus
                              </Text>
                            </VStack>
                            {engagementLevel && renderPredictedEngagementBadge(engagementLevel)}
                          </HStack>
                        </VStack>
                      </CardHeader>

                      <CardBody pt={0}>
                        <VStack align="stretch" gap={4}>
                          <Text
                            fontSize="sm"
                            color="gray.700"
                            lineHeight="1.5"
                            noOfLines={4}
                            title={post.text}
                          >
                            {post.text}
                          </Text>

                          {post.hashtags?.length > 0 && (
                            <Wrap spacing={1}>
                              {post.hashtags.slice(0, 3).map((tag) => (
                                <WrapItem key={`${tag}`}>
                                  <Badge
                                    variant="subtle"
                                    colorPalette="blue"
                                    borderRadius="full"
                                    fontSize="xs"
                                    px={2}
                                    py={1}
                                  >
                                    {tag}
                                  </Badge>
                                </WrapItem>
                              ))}
                              {post.hashtags.length > 3 && (
                                <WrapItem>
                                  <Badge
                                    variant="subtle"
                                    colorPalette="gray"
                                    borderRadius="full"
                                    fontSize="xs"
                                    px={2}
                                    py={1}
                                  >
                                    +{post.hashtags.length - 3}
                                  </Badge>
                                </WrapItem>
                              )}
                            </Wrap>
                          )}

                          <Separator />

                          <VStack align="stretch" spacing={2}>
                            {renderMediaSuggestion(post)}

                            <Button
                              size="sm"
                              bg="black"
                              color="white"
                              _hover={{ bg: "gray.800" }}
                              _active={{ bg: "gray.900" }}
                              fontWeight="semibold"
                              mt={2}
                            >
                              Post
                            </Button>

                            {post.rationale && (
                              <Collapsible.Root
                                open={expandedCards[index]}
                                onOpenChange={() => toggleCard(index)}
                              >
                                <CollapsibleTrigger asChild>
                                  <Button
                                    variant="ghost"
                                    size="xs"
                                    p={0}
                                    h="auto"
                                    fontWeight="semibold"
                                    color="gray.600"
                                    _hover={{ color: "gray.800" }}
                                    justifyContent="flex-start"
                                    gap={1}
                                  >
                                    <Text
                                      fontSize="xs"
                                      textTransform="uppercase"
                                      letterSpacing="wide"
                                    >
                                      Reasoning
                                    </Text>
                                    <Icon
                                      as={FiChevronDown}
                                      boxSize={3}
                                      transform={expandedCards[index] ? "rotate(180deg)" : "rotate(0deg)"}
                                      transition="transform 0.2s ease"
                                    />
                                  </Button>
                                </CollapsibleTrigger>
                                <CollapsibleContent>
                                  <Text
                                    fontSize="xs"
                                    color="gray.600"
                                    lineHeight="1.4"
                                    mt={2}
                                    pl={2}
                                    borderLeft="2px solid"
                                    borderColor="gray.200"
                                  >
                                    {post.rationale}
                                  </Text>
                                </CollapsibleContent>
                              </Collapsible.Root>
                            )}
                          </VStack>
                        </VStack>
                      </CardBody>
                    </Card.Root>
                  )
                })}
              </Flex>
            </Box>
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

      {/* Recent News Section */}
      <Box px={{ base: 6, md: 12 }} py={{ base: 8, md: 12 }}>
        <VStack align="stretch" gap={6}>
          <VStack align="stretch" gap={3}>
            <Heading size="lg" color="gray.800">
              Add Recent News & Trends
            </Heading>
            <Text color="gray.600">
              Stay updated with the latest industry insights to enhance your content strategy.
            </Text>
          </VStack>

          <SimpleGrid columns={{ base: 1, md: 2, lg: 3 }} gap={4}>
            {generateRecentNews().map((news) => (
              <Box
                key={news.id}
                bg="white"
                borderRadius="xl"
                border="1px solid"
                borderColor="gray.200"
                p={4}
                _hover={{
                  borderColor: 'gray.300',
                  boxShadow: '0 4px 12px -2px rgba(0, 0, 0, 0.1)',
                  transform: 'translateY(-2px)'
                }}
                transition="all 0.2s ease"
                cursor="pointer"
              >
                <VStack align="stretch" gap={3}>
                  <HStack justify="space-between" align="flex-start">
                    <Badge
                      colorScheme="blue"
                      variant="subtle"
                      fontSize="xs"
                      px={2}
                      py={1}
                    >
                      {news.category}
                    </Badge>
                    <Text fontSize="xs" color="gray.500">
                      {news.timeAgo}
                    </Text>
                  </HStack>

                  <Text
                    fontSize="sm"
                    fontWeight="semibold"
                    color="gray.800"
                    lineHeight="1.4"
                    noOfLines={2}
                  >
                    {news.title}
                  </Text>

                  <Text fontSize="xs" color="gray.600">
                    {news.source}
                  </Text>
                </VStack>
              </Box>
            ))}
          </SimpleGrid>
        </VStack>
      </Box>
    </Box>
  )
}

export default AnalysisPage
