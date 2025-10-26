export const demoTimelineData = [
  {
    id: 'task-001',
    request_id: '4489028f-ab79-4765-b256-ce7d343ba453',
    name: 'Data Retriving',
    message: 'Process customer data for analytics',
    status: 'completed',
    timestamp: '2024-01-15T10:45:00',
    events: [],
  },
  {
    id: 'task-002',
    request_id: '4489028f-ab79-4765-b256-ce7d343ba453',
    name: 'Data Analysis',
    message: '',
    status: 'pending',
    timestamp: '2024-01-15T10:45:00',
    events: [
      {
        id: 1,
        name: 'reasoning 1',
        status: 'info',
        message: 'Task initialization completed',
        timestamp: '2024-01-15T10:30:00',
      },
      {
        id: 2,
        name: 'reasoning 2',
        status: 'success',
        message: 'Task completed successfully',
        timestamp: '2024-01-15T10:45:00',
      },
    ],
  },
]
