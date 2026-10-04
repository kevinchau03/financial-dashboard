import { useId, useRef, useState } from 'react'

type CsvUploadProps = {
  onFileSelect?: (file: File | null) => void
  disabled?: boolean
}

export default function CsvUpload({ onFileSelect, disabled = false }: CsvUploadProps) {
  const id = useId()
  const input = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [error, setError] = useState('')

  function selectFile(selected: File | undefined) {
    if (!selected) return
    let message = ''
    if (!selected.name.toLowerCase().endsWith('.csv')) message = 'Please choose a CSV file.'
    else if (selected.size === 0) message = 'This file is empty. Please choose a CSV with data.'
    else if (selected.size > 5 * 1024 * 1024) message = 'Please choose a file smaller than 5 MB.'
    setError(message)
    setFile(message ? null : selected)
    onFileSelect?.(message ? null : selected)
    if (message && input.current) input.current.value = ''
  }

  function removeFile() {
    setFile(null)
    setError('')
    if (input.current) input.current.value = ''
    onFileSelect?.(null)
  }

  return <div className="csv-upload">
    <label htmlFor={id}>Choose your CSV file</label>
    <p id={`${id}-help`} className="upload-help">CSV files only · Up to 5 MB</p>
    <input ref={input} id={id} type="file" disabled={disabled} accept=".csv,text/csv" aria-describedby={`${id}-help${error ? ` ${id}-error` : ''}`}
      aria-invalid={!!error} onChange={event => selectFile(event.target.files?.[0])} />
    {error && <p id={`${id}-error`} role="alert">{error}</p>}
    <div role="status">
      {file && <div className="selected-file">
        <div><strong>{file.name}</strong><p>{Math.max(1, Math.ceil(file.size / 1024))} KB · Selected</p></div>
        <button type="button" className="secondary" disabled={disabled} onClick={removeFile}>Remove file</button>
      </div>}
    </div>
    <p className="upload-help">Upload your TD statement to save its transactions and view its contents.</p>
  </div>
}
