import { useState } from 'react'
import { Button, Field, Input, Stack } from '@chakra-ui/react'
import { BsClipboardDataFill } from "react-icons/bs";

const LinkInput = ({ 
  label, 
  placeholder = 'Paste your link here...', 
  onAnalyze,
  isDisabled = false
}) => {
  const [value, setValue] = useState('')

  const handleAnalyze = () => {
    if (typeof onAnalyze === 'function') {
      onAnalyze(value)
    }
  }

  return (
    <Field.Root>
      {label ? (
        <Field.Label fontWeight="semibold" color="gray.600">
          {label}
        </Field.Label>
      ) : null}
      <Stack
        direction={{ base: 'column', sm: 'row' }}
        gap={4}
        align="stretch"
        w="full"
      >
        <Input
          value={value}
          onChange={(event) => setValue(event.target.value)}
          placeholder={placeholder}
          size="lg"
          bg="white"
          rounded="full"
          ps={6}
          flex={{ base: '1 1 auto', sm: '0 0 80%' }}
          w="100%"
          boxShadow="sm"
          _hover={{ boxShadow: 'md' }}
          _focus={{ boxShadow: 'outline' }}
          disabled={isDisabled}
        />
        <Button
          bg="var(--brand-secondary)"
          color="white"
          size="lg"
          rounded="full"
          px={8}
          flex={{ base: '1 1 auto', sm: '0 0 20%' }}
          w="100%"
          _hover={{ bg: 'var(--brand-secondary-hover)' }}
          _active={{ bg: 'var(--brand-secondary-hover)' }}
          disabled={isDisabled}
          onClick={handleAnalyze}
        >
          Analyze <BsClipboardDataFill style={{ marginLeft: 2 }} />
        </Button>
      </Stack>
    </Field.Root>
  )
}

export default LinkInput
