'use client'

import { useState } from 'react'
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import Papa from 'papaparse'

interface Recipient {
  id: string
  name: string
  phone_number: string
}

export function GroupMessageFormComponent() {
  const [message, setMessage] = useState('')
  const [selectedRecipients, setSelectedRecipients] = useState<string[]>([])
  const [csvData, setCsvData] = useState<any[]>([])
  const [allNumbers, setAllNumbers] = useState(false)
  const [recipients, setRecipients] = useState<Recipient[]>([
    { id: '1', name: 'Alice Johnson', phone_number: '+15555555555' },
    { id: '2', name: 'Bob Smith', phone_number: '+15555555556' },
    { id: '3', name: 'John Doe', phone_number: '+15555555557' },
    { id: '4', name: 'Charlie Wilson', phone_number: '+15555555558' },
    { id: '5', name: 'Ethan Hunt', phone_number: '+15555555559' },
  ])

  const handleSelectAll = () => {
    setSelectedRecipients(recipients.map(r => r.id))
    setAllNumbers(true)
  }

  const handleUndoSelections = () => {
    setSelectedRecipients([])
    setAllNumbers(false)
  }

  const handleRecipientToggle = (recipientId: string) => {
    setSelectedRecipients(prev =>
      prev.includes(recipientId)
        ? prev.filter(id => id !== recipientId)
        : [...prev, recipientId]
    )
  }

  const columnNameMapping = {
    'Client name': 'name',
    'Name': 'name',
    'Client email address': 'email',
    'Email': 'email',
    'Client phone number': 'phone_number',
    'Phone Number': 'phone_number'
  }
  
  const handleCsvChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0]
      Papa.parse(file, {
        header: true,
        skipEmptyLines: true,
        complete: (results) => {
          const data = results.data

          interface ColumnNameMapping {
            'Client name': string;
            Name: string;
            'Client email address': string;
            Email: string;
            'Client phone number': string;
            'Phone Number': string;
          }
          
          // Example mapping
          const columnNameMapping: ColumnNameMapping = {
            'Client name': 'name',
            Name: 'name',
            'Client email address': 'email',
            Email: 'email',
            'Client phone number': 'phone_number',
            'Phone Number': 'phone_number'
          }
          
          const normalizedData = data.map((row: any) => {
            const normalizedRow: any = {}
            for (const key in row) {
              const trimmedKey = key.trim() as keyof ColumnNameMapping
              const normalizedKey = columnNameMapping[trimmedKey]
              if (normalizedKey) {
                normalizedRow[normalizedKey] = row[key].trim()
              }
            }
            return normalizedRow;
          })
  
          // Filter out rows without required fields
          const filteredData = normalizedData.filter((row: any) => {
            return row.name && row.phone_number
          })
  
          setCsvData(filteredData)
  
          // Optionally update recipients state
          setRecipients(filteredData.map((row: any, index: number) => ({
            id: index.toString(),
            name: row.name,
            phone_number: row.phone_number,
            email: row.email || '',
          })))
        },
        error: (error) => {
          console.error('Error parsing CSV:', error)
        }
      })
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()

    const formData = {
      message,
      all_numbers: allNumbers,
      select_numbers: selectedRecipients,
      csv_data: csvData,
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
        <Label htmlFor="csv-upload">Upload CSV</Label>
        <Input
          id="csv-upload"
          type="file"
          accept=".csv"
          onChange={handleCsvChange}
        />
      </div>

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
