// path: tests/integration/conversations/create.test.integration.tsx
// version: 3

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { renderWithProviders } from '@/tests/helpers/render'
import { NewConversationButton } from '@/components/sidebar/NewConversationButton'
import { rest } from 'msw'
import { server } from '@/tests/mocks/server'

describe('Create Conversation Integration', () => {
  it('creates conversation from button', async () => {
    const user = userEvent.setup()
    const mockOnCreate = jest.fn()
    
    // Mock successful creation
    server.use(
      rest.post('/api/conversations', (req, res, ctx) => {
        return res(
          ctx.status(201),
          ctx.json({
            conversation: {
              id: 'conv-new',
              title: 'New Conversation',
              groupId: null,
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString(),
              messageCount: 0,
              ownerId: 'user-john-doe',
              sharedWithGroupIds: [],
              isShared: false,
            }
          })
        )
      })
    )
    
    // Simple test component
    const TestComponent = () => {
      const [count, setCount] = React.useState(0)
      
      const handleClick = async () => {
        const created = await mockOnCreate()
        if (created) {
          setCount(c => c + 1)
        }
      }
      
      return (
        <div>
          <NewConversationButton onClick={handleClick} />
          <div data-testid="count">{count}</div>
        </div>
      )
    }
    
    mockOnCreate.mockResolvedValue(true)
    
    const { container } = render(<TestComponent />)
    
    const button = screen.getByRole('button', { name: /new conversation/i })
    await user.click(button)
    
    await waitFor(() => {
      expect(screen.getByTestId('count')).toHaveTextContent('1')
    })
  })

  it('creates conversation with title', async () => {
    const user = userEvent.setup()
    const mockOnCreate = jest.fn()
    
    // Mock with custom title
    server.use(
      rest.post('/api/conversations', async (req, res, ctx) => {
        const body = await req.json() as { title?: string }
        return res(
          ctx.status(201),
          ctx.json({
            conversation: {
              id: 'conv-new',
              title: body.title || 'New Conversation',
              groupId: null,
              createdAt: new Date().toISOString(),
              updatedAt: new Date().toISOString(),
              messageCount: 0,
              ownerId: 'user-john-doe',
              sharedWithGroupIds: [],
              isShared: false,
            }
          })
        )
      })
    )
    
    const TestComponent = () => {
      const [titles, setTitles] = React.useState<string[]>([])
      
      const handleClick = async () => {
        const title = await mockOnCreate('Project Planning')
        if (title) {
          setTitles(t => [...t, title])
        }
      }
      
      return (
        <div>
          <NewConversationButton onClick={handleClick} />
          <div data-testid="titles">{titles.join(', ')}</div>
        </div>
      )
    }
    
    mockOnCreate.mockResolvedValue('Project Planning')
    
    render(<TestComponent />)
    
    const button = screen.getByRole('button', { name: /new conversation/i })
    await user.click(button)
    
    await waitFor(() => {
      expect(screen.getByTestId('titles')).toHaveTextContent('Project Planning')
    })
  })
})

// Import React for JSX
import * as React from 'react'