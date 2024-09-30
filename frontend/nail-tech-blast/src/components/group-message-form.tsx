'use client'

import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"

interface Recipient {
  id: string
  name: string
}

const recipients: Recipient[] = [
  { id: '1', name: 'Alice Johnson' },
  { id: '2', name: 'Bob Smith' },
  { id: '3', name: 'Charlie Brown' },
  { id: '4', name: 'Diana Ross' },
  { id: '5', name: 'Ethan Hunt' },
]

export function GroupMessageFormComponent() {
  const [message, setMessage] = useState('')
  const [selectedRecipients, setSelectedRecipients] = useState<string[]>([])

  const handleSelectAll = () => {
    setSelectedRecipients(recipients.map(r => r.id))
  }

  const handleUndoSelections = () => {
    setSelectedRecipients([])
  }

  const handleRecipientToggle = (recipientId: string) => {
    setSelectedRecipients(prev =>
      prev.includes(recipientId)
        ? prev.filter(id => id !== recipientId)
        : [...prev, recipientId]
    )
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const formData = {
      message,
      recipients: selectedRecipients
    }

    try {
      const response = await fetch('https://10g2414t07.execute-api.us-east-1.amazonaws.com/DEV/messages', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        throw new Error('Error in sending the message.');
      }

      const result = await response.json();
      console.log('Message sent successfully:', result);

    } catch (error) {
      console.error('Error:', error);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 max-w-md mx-auto p-6 bg-white rounded-lg shadow">
      <div className="space-y-2">
        <Label htmlFor="message">Message</Label>
        <Textarea
          id="message"
          placeholder="Type your message here..."
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          className="min-h-[100px]"
        />
      </div>

      <div className="space-y-2">
        <Label>Recipients</Label>
        <div className="flex space-x-2 mb-2">
          <Button type="button" variant="outline" size="sm" onClick={handleSelectAll}>
            Select All
          </Button>
          <Button type="button" variant="outline" size="sm" onClick={handleUndoSelections}>
            Undo Selections
          </Button>
        </div>
        <div className="space-y-2 max-h-40 overflow-y-auto border rounded p-2">
          {recipients.map((recipient) => (
            <div key={recipient.id} className="flex items-center space-x-2">
              <Checkbox
                id={recipient.id}
                checked={selectedRecipients.includes(recipient.id)}
                onCheckedChange={() => handleRecipientToggle(recipient.id)}
              />
              <Label htmlFor={recipient.id} className="text-sm font-normal">
                {recipient.name}
              </Label>
            </div>
          ))}
        </div>
      </div>

      <Button type="submit" className="w-full">
        Send Message
      </Button>
    </form>
  )
}
