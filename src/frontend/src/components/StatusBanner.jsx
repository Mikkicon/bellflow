import { Alert, Button } from '@chakra-ui/react'

const StatusBanner = ({
  type = 'success',
  title,
  message,
  actionLabel,
  onAction,
  onClose,
}) => {
  // Keep styling minimal and compatible with v3 slot API

  return (
    <Alert.Root
      status={type}
      variant="subtle"
      borderRadius="lg"
      px={4}
      py={3}
      mt={4}
      alignItems="center"
      gap={3}
    >
      <Alert.Indicator />
      <Alert.Content color="fg" flex="1" minW={0} textAlign="left">
        {title ? <Alert.Title textAlign="left">{title}</Alert.Title> : null}
        {message ? (
          <Alert.Description color="gray.600" textAlign="left">{message}</Alert.Description>
        ) : null}
      </Alert.Content>
      {actionLabel ? (
        <Button size="sm" onClick={onAction} alignSelf="center">
          {actionLabel}
        </Button>
      ) : null}
      {onClose ? (
        <Button size="sm" variant="ghost" onClick={onClose} alignSelf="center">
          Dismiss
        </Button>
      ) : null}
    </Alert.Root>
  )
}

export default StatusBanner
