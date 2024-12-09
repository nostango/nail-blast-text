'use client'

import { useState, useEffect } from 'react'
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Input } from "@/components/ui/input"
import Papa from 'papaparse'
// import { v4 as uuidv4 } from 'uuid' // Removed UUID import

// Define the shape of a recipient as returned by the API
interface ApiRecipient {
  id: string // Ensure the API returns the 'id'
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
  first_name: string
  last_name: string
  phone_number: string
  email?: string
  notes?: string
  days_since_last_appointment?: string
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
  const [isUploadingCsv, setIsUploadingCsv] = useState(false)
  const [isSendingMessage, setIsSendingMessage] = useState(false)
  const [isCsvParsed, setIsCsvParsed] = useState(false)

  useEffect(() => {
    fetchRecipients()
  }, [])

  const fetchRecipients = async () => {
    try {
      const response = await fetch('https://10g2414t07.execute-api.us-east-1.amazonaws.com/DEV/messages', {
        method: 'GET',
      })
      if (!response.ok) {
        throw new Error('Failed to fetch recipients.')
      }
      const data: ApiRecipient[] = await response.json()
      console.log('Fetched Recipients:', data) // Debugging log
      setRecipients(data.map((item) => ({
        id: item.id, // Use the backend-generated ID
        name: item.name,
        phone_number: item.phone_number,
        email: item.email || '',
      })))
    } catch (error) {
      console.error('Error fetching recipients:', error)
    }
  }

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
      console.log('Selected file:', file)
      Papa.parse<CsvRowRaw>(file, {
        header: true,
        skipEmptyLines: true,
        complete: async (results) => { // Make the callback async
          console.log('Papa parse results:', results)
          const data: CsvRowRaw[] = results.data

          const columnNameMapping: { [key: string]: keyof CsvRow } = {
            'First Name': 'first_name',
            'Last Name': 'last_name',
            'Phone': 'phone_number',
            'Email': 'email',
            'Notes': 'notes',
            'Days Since Last Appointment': 'days_since_last_appointment'
            // 'Banned' is intentionally omitted
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

          console.log('Normalized Data:', normalizedData)

          // Filter out rows without required fields
          const filteredData = normalizedData.filter((row) => {
            return row.first_name && row.last_name && row.phone_number
          })

          console.log('Filtered Data:', filteredData)

          setCsvData(filteredData)
          setIsCsvParsed(filteredData.length > 0)

          // No longer setting recipients here
        },
        error: (error) => {
          console.error('Error parsing CSV:', error)
        }
      })
    }
  }

  const handleSendMessage = async (e: React.FormEvent) => {
    e.preventDefault()

    if (!message.trim()) {
      alert('Message cannot be empty.')
      return
    }

    const formData = {
      action: 'send_message',
      message,
      all_numbers: allNumbers,
      select_numbers: selectedRecipients,
      csv_data: csvData,
    }

    setIsSendingMessage(true)

    try {
      const response = await fetch('https://10g2414t07.execute-api.us-east-1.amazonaws.com/DEV/messages', {
        method: 'POST',
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      })

      if (!response.ok) {
        // Attempt to parse error message from response
        const errorData = await response.json()
        throw new Error(errorData.message || 'Error in sending the message.')
      }

      const result = await response.json()
      console.log('Message sent successfully:', result)
      // Display success message to the user as a green confirmation box on the page
      alert('Message sent successfully!')

      // Reset form if needed
      setMessage('')
      setSelectedRecipients([])
      setAllNumbers(false)
      setCsvData([])
      setIsCsvParsed(false)

      // Fetch updated recipients to include any new entries
      await fetchRecipients()

    } catch (error: unknown) {
      if (error instanceof Error) {
        console.error('Error:', error.message);
        alert(`Failed to send message: ${error.message}`);
      } else {
        console.error('Unknown error:', error);
        alert('Failed to send message: Unknown error.');
      }
    } finally {
      setIsSendingMessage(false)
    }
  }

  const handleUploadCsv = async () => {
    console.log('Uploading CSV Data:', csvData)
    if (csvData.length === 0) {
      alert('No CSV data to upload.')
      return
    }

    const formData = {
      action: 'upload_csv',
      csv_data: csvData,
    }

    setIsUploadingCsv(true)

    try {
      const response = await fetch('https://10g2414t07.execute-api.us-east-1.amazonaws.com/DEV/messages', {
        method: 'POST',
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(formData),
      })

      if (!response.ok) {
        // Attempt to parse error message from response
        const errorData = await response.json()
        throw new Error(errorData.message || 'Error in uploading the CSV.')
      }

      const result = await response.json()
      console.log('CSV uploaded successfully:', result)
      alert('CSV uploaded successfully!')

      // Fetch updated recipients with backend-generated IDs
      await fetchRecipients()

      // Reset CSV data if needed
      setCsvData([])
      setIsCsvParsed(false)

    } catch (error: unknown) {
      if (error instanceof Error) {
        console.error('Error:', error.message);
        alert(`Failed to upload CSV: ${error.message}`);
      } else {
        console.error('Unknown error:', error);
        alert('Failed to upload CSV: Unknown error.');
      }
    } finally {
      setIsUploadingCsv(false)
    }
  }

  return (
    <form id="text-submission" onSubmit={handleSendMessage} className="space-y-6 max-w-md mx-auto p-6 bg-white rounded-lg shadow">
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

      <div className="flex space-x-4">
        <Button type="submit" className="w-full" disabled={isSendingMessage}>
          {isSendingMessage ? 'Sending...' : 'Send Message'}
        </Button>
        <Button type="button" className="w-full" onClick={handleUploadCsv} disabled={!isCsvParsed || isUploadingCsv}>
          {isUploadingCsv ? 'Uploading...' : 'Upload CSV'}
        </Button>
      </div>
    </form>
  )
}
