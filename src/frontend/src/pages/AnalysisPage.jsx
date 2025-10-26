import {
  Badge,
  Box,
  Button,
  Heading,
  HStack,
  Icon,
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
} from '@chakra-ui/react'
import { Link as RouterLink, useParams } from 'react-router-dom'
import { useState } from 'react'
import { FiFileText, FiFilm, FiImage, FiVideo, FiChevronDown, FiHeart, FiMessageCircle, FiRepeat } from 'react-icons/fi'
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
  const [expandedCards, setExpandedCards] = useState({})

  const toggleCard = (index) => {
    setExpandedCards(prev => ({
      ...prev,
      [index]: !prev[index]
    }))
  }

  const generateEngagementMetrics = () => {
    return {
      likes: Math.floor(Math.random() * 5000) + 100,
      comments: Math.floor(Math.random() * 500) + 10,
      reposts: Math.floor(Math.random() * 200) + 5
    }
  }

  const formatCount = (count) => {
    if (count >= 1000) {
      return (count / 1000).toFixed(1) + 'k'
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

  const renderMediaSuggestion = (media) => {
    const normalizedMedia = typeof media === 'string' ? media.toLowerCase() : ''
    const MediaIcon = mediaIconMap[normalizedMedia] || FiFileText
    const metrics = generateEngagementMetrics()

    return (
      <VStack align="stretch" spacing={2}>
        <HStack spacing={1.5} color="gray.500">
          <Icon as={MediaIcon} boxSize={4} />
          <Text fontSize="xs" fontWeight="medium" textTransform="capitalize">
            {normalizedMedia || 'Not specified'}
          </Text>
        </HStack>

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
          {suggestedPosts.length > 0 ? (
            <Box w="full">
              <Flex
                direction={{ base: 'column', lg: 'row' }}
                gap={6}
                align="stretch"
                justify="space-between"
                w="full"
                overflowX={{ base: 'visible', lg: 'auto' }}
                pb={2}
              >
                {suggestedPosts.map((post, index) => {
                  const mediaLabel = capitalize(post?.media_suggestion) || 'Content'

                  return (
                     <Card.Root
                       key={`${post.media_suggestion}-${index}`}
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
                            {renderPredictedEngagementBadge(post.predicted_engagement)}
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
                            {renderMediaSuggestion(post.media_suggestion)}
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
    </Box>
  )
}

export default AnalysisPage