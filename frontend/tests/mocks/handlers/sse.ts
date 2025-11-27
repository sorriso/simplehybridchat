// path: tests/mocks/handlers/sse.ts
// version: 3 - With full base URL

import { rest } from 'msw'

const BASE_URL = 'http://localhost:8000'

/**
 * SSE message types
 */
interface SSEChunk {
  type: 'text' | 'code' | 'markdown' | 'thinking' | 'error' | 'done'
  content: string
  delay?: number
}

/**
 * Mock SSE responses for different conversation types
 */
const sseResponses: Record<string, SSEChunk[]> = {
  simple: [
    { type: 'text', content: 'Hello! ', delay: 100 },
    { type: 'text', content: 'How can ', delay: 80 },
    { type: 'text', content: 'I help ', delay: 80 },
    { type: 'text', content: 'you today?', delay: 100 },
    { type: 'done', content: '', delay: 50 },
  ],
  code: [
    { type: 'text', content: 'Here is a Python example:\n\n', delay: 120 },
    { type: 'code', content: '```python\n', delay: 100 },
    { type: 'code', content: 'def hello_world():\n', delay: 80 },
    { type: 'code', content: '    print("Hello, World!")\n', delay: 80 },
    { type: 'code', content: '```\n', delay: 100 },
    { type: 'text', content: '\nThis function prints a greeting.', delay: 150 },
    { type: 'done', content: '', delay: 50 },
  ],
  markdown: [
    { type: 'markdown', content: '# Main Title\n\n', delay: 100 },
    { type: 'markdown', content: 'This is a **bold** statement ', delay: 80 },
    { type: 'markdown', content: 'with *italic* text.\n\n', delay: 80 },
    { type: 'markdown', content: '## Section\n\n', delay: 100 },
    { type: 'markdown', content: '- Item 1\n', delay: 70 },
    { type: 'markdown', content: '- Item 2\n', delay: 70 },
    { type: 'markdown', content: '- Item 3\n', delay: 70 },
    { type: 'done', content: '', delay: 50 },
  ],
  thinking: [
    { type: 'thinking', content: '[Analyzing your question...]', delay: 200 },
    { type: 'text', content: 'Based on my analysis, ', delay: 120 },
    { type: 'text', content: 'the answer is yes.', delay: 100 },
    { type: 'done', content: '', delay: 50 },
  ],
  long: [
    { type: 'text', content: 'Let me explain this in detail. ', delay: 100 },
    { type: 'text', content: 'First, we need to understand the basics. ', delay: 100 },
    { type: 'text', content: 'Then we can move to advanced topics. ', delay: 100 },
    { type: 'text', content: 'Finally, we will discuss best practices.', delay: 100 },
    { type: 'done', content: '', delay: 50 },
  ],
  error: [
    { type: 'text', content: 'Processing your request', delay: 100 },
    { type: 'error', content: 'Error: Connection timeout', delay: 200 },
  ],
}

/**
 * Create SSE stream from chunks
 */
function createSSEStream(chunks: SSEChunk[]): ReadableStream<Uint8Array> {
  const encoder = new TextEncoder()

  return new ReadableStream({
    async start(controller) {
      try {
        for (const chunk of chunks) {
          // Simulate network delay
          if (chunk.delay) {
            await new Promise(resolve => setTimeout(resolve, chunk.delay))
          }

          // Format SSE message
          let sseMessage = ''
          
          if (chunk.type === 'error') {
            sseMessage = `event: error\ndata: ${JSON.stringify({ error: chunk.content })}\n\n`
          } else if (chunk.type === 'done') {
            sseMessage = `data: [DONE]\n\n`
          } else {
            sseMessage = `data: ${JSON.stringify({ 
              type: chunk.type, 
              content: chunk.content 
            })}\n\n`
          }

          controller.enqueue(encoder.encode(sseMessage))

          // Stop on error or done
          if (chunk.type === 'error' || chunk.type === 'done') {
            break
          }
        }
      } catch (error) {
        controller.error(error)
      } finally {
        controller.close()
      }
    },
  })
}

/**
 * SSE endpoint handlers
 */
export const sseHandlers = [
  // Chat SSE endpoint
  rest.post(`${BASE_URL}/api/chat/stream`, async (req, res, ctx) => {
    const body = await req.json() as { message: string; conversationId: string }
    
    console.log('[SSE Handler] Received request:', body)
    
    // Determine response type based on message content
    let responseType = 'simple'
    const msg = body.message.toLowerCase()
    
    if (msg.includes('code') || msg.includes('python') || msg.includes('javascript')) {
      responseType = 'code'
    } else if (msg.includes('markdown') || msg.includes('format')) {
      responseType = 'markdown'
    } else if (msg.includes('think') || msg.includes('analyze')) {
      responseType = 'thinking'
    } else if (msg.includes('long') || msg.includes('detail')) {
      responseType = 'long'
    } else if (msg.includes('error') || msg.includes('fail')) {
      responseType = 'error'
    }

    const chunks = sseResponses[responseType] || sseResponses.simple

    return res(
      ctx.status(200),
      ctx.set('Content-Type', 'text/event-stream'),
      ctx.set('Cache-Control', 'no-cache'),
      ctx.set('Connection', 'keep-alive'),
      ctx.body(createSSEStream(chunks))
    )
  }),

  // Custom SSE response for testing (allows injecting specific chunks)
  rest.post(`${BASE_URL}/api/chat/stream/custom`, async (req, res, ctx) => {
    const body = await req.json() as { chunks: SSEChunk[] }
    
    return res(
      ctx.status(200),
      ctx.set('Content-Type', 'text/event-stream'),
      ctx.set('Cache-Control', 'no-cache'),
      ctx.set('Connection', 'keep-alive'),
      ctx.body(createSSEStream(body.chunks))
    )
  }),
]

/**
 * Helper to create custom SSE chunks for testing
 */
export function createSSEChunks(content: string, chunkSize = 10, delayMs = 50): SSEChunk[] {
  const chunks: SSEChunk[] = []
  
  for (let i = 0; i < content.length; i += chunkSize) {
    chunks.push({
      type: 'text',
      content: content.slice(i, i + chunkSize),
      delay: delayMs,
    })
  }
  
  chunks.push({ type: 'done', content: '', delay: 50 })
  
  return chunks
}