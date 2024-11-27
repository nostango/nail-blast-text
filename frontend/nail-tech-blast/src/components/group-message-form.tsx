'use client'

import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import Papa from 'papaparse'

// Define the shape of a recipient as returned by the API
interface ApiRecipient {
  name: string
  phone_number: string
  email?: string
}

// Define the shape of a recipient used within the component
interface Recipient {
  id: string
  name: string
  phone_number: string
  email?: string
}

// Define the shape of a CSV row after normalization
interface CsvRow {
  name: string
  phone_number: string
  email?: string
}

// Define the shape of a raw CSV row before normalization
interface CsvRowRaw {
  [key: string]: string
}

export function GroupMessageFormComponent() {
  const [message, setMessage] = useState('')
  const [selectedRecipients, setSelectedRecipients] = useState<string[]>([])
  const [csvData, setCsvData] = useState<CsvRow[]>([])
  const [allNumbers, setAllNumbers] = useState(false)
  const [recipients, setRecipients] = useState<Recipient[]>([])

  useEffect(() => {
    const fetchRecipients = async () => {
      try {
        const response = await fetch('https://10g2414t07.execute-api.us-east-1.amazonaws.com/DEV/messages', {
          method: 'GET',
        })
        const data: ApiRecipient[] = await response.json()
        setRecipients(data.map((item, index) => ({
          id: index.toString(),
          name: item.name,
          phone_number: item.phone_number,
          email: item.email || '',
        })))
      } catch (error) {
        console.error('Error fetching recipients:', error)
      }
    }

    fetchRecipients()
  }, [])

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

  const handleCsvChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0]
      Papa.parse<CsvRowRaw>(file, {
        header: true,
        skipEmptyLines: true,
        complete: (results) => {
          const data: CsvRowRaw[] = results.data

          const columnNameMapping: { [key: string]: keyof CsvRow } = {
            'Client name': 'name',
            'Name': 'name',
            'Client email address': 'email',
            'Email': 'email',
            'Client phone number': 'phone_number',
            'Phone Number': 'phone_number'
          }

          const normalizedData: CsvRow[] = data.map((row) => {
            const normalizedRow: Partial<CsvRow> = {}
            for (const key in row) {
              const trimmedKey = key.trim()
              const normalizedKey = columnNameMapping[trimmedKey]
              if (normalizedKey) {
                normalizedRow[normalizedKey] = row[key]?.trim() || ''
              }
            }
            return normalizedRow as CsvRow
          })

          // Filter out rows without required fields
          const filteredData = normalizedData.filter((row) => {
            return row.name && row.phone_number
          })

          setCsvData(filteredData)

          // Optionally update recipients state
          setRecipients(filteredData.map((row, index) => ({
            id: (recipients.length + index).toString(), // Ensure unique IDs
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
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      })

      if (!response.ok) {
        throw new Error('Error in sending the message.')
      }

      const result = await response.json()
      console.log('Message sent successfully:', result)

      // Reset form if needed
      setMessage('')
      setSelectedRecipients([])
      setAllNumbers(false)
      setCsvData([])

    } catch (error) {
      console.error('Error:', error)
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
