import { useState } from 'react'
import './App.css'

function App() {
  const [file, setFile] = useState<File | null>(null)
  const [isProcessing, setIsProcessing] = useState(false)
  const [progress, setProgress] = useState(0)
  const [audioUrl, setAudioUrl] = useState<string | null>(null)
  const [mode, setMode] = useState('solo')
  const [duration, setDuration] = useState(300)

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (event.target.files && event.target.files[0]) {
      setFile(event.target.files[0])
    }
  }

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()
    if (!file) return

    setIsProcessing(true)
    setProgress(0)
    setAudioUrl(null)

    const formData = new FormData()
    formData.append('input_file', file)
    formData.append('mode', mode)
    formData.append('duration', duration.toString())

    try {
      // Simulate progress for demo
      const interval = setInterval(() => {
        setProgress(prev => {
          if (prev >= 95) {
            clearInterval(interval)
            return prev
          }
          return prev + Math.random() * 10
        })
      }, 500)

      const response = await fetch('/api/v1/podcast', {
        method: 'POST',
        body: formData,
      })

      clearInterval(interval)
      setProgress(100)

      if (response.ok) {
        const data = await response.json()
        // In a real app, we'd get the audio URL from the response
        // For now, we'll just simulate it
        setAudioUrl('/api/v1/podcast/sample.mp3')
      } else {
        console.error('Error generating podcast')
      }
    } catch (error) {
      console.error('Error:', error)
    } finally {
      setIsProcessing(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900">
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-2xl mx-auto">
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-white mb-4">
              Research2Podcast
            </h1>
            <p className="text-xl text-purple-200">
              Transform academic documents into engaging podcasts
            </p>
          </div>

          <div className="bg-white/10 backdrop-blur-lg rounded-2xl p-8 shadow-2xl border border-white/20">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-semibold text-purple-100 mb-3">
                  Upload Document
                </label>
                <div className="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-dashed border-purple-400 rounded-lg hover:border-purple-300 transition-colors duration-200">
                  <div className="space-y-1 text-center">
                    <svg
                      className="mx-auto h-12 w-12 text-purple-300"
                      stroke="currentColor"
                      fill="none"
                      viewBox="0 0 48 48"
                      aria-hidden="true"
                    >
                      <path
                        d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                        strokeWidth={2}
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                    <div className="flex text-sm text-purple-200">
                      <label
                        htmlFor="file-upload"
                        className="relative cursor-pointer bg-purple-600 rounded-md font-medium text-white hover:bg-purple-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-purple-500 px-3 py-2"
                      >
                        <span>Upload a file</span>
                        <input
                          id="file-upload"
                          name="file-upload"
                          type="file"
                          className="sr-only"
                          accept=".pdf,.md,.html,.txt"
                          onChange={handleFileChange}
                          disabled={isProcessing}
                        />
                      </label>
                      <p className="pl-1 pt-1">or drag and drop</p>
                    </div>
                    <p className="text-xs text-purple-300">
                      PDF, Markdown, HTML, or TXT up to 10MB
                    </p>
                  </div>
                </div>
                {file && (
                  <p className="mt-2 text-sm text-green-300">
                    Selected: {file.name}
                  </p>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label className="block text-sm font-semibold text-purple-100 mb-3">
                    Podcast Mode
                  </label>
                  <select
                    value={mode}
                    onChange={(e) => setMode(e.target.value)}
                    disabled={isProcessing}
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500 bg-white/20 text-white border border-white/30"
                  >
                    <option value="solo">Solo Narration</option>
                    <option value="single-llm">Dual Hosts</option>
                    <option value="multi-agent">Multi-Agent</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-semibold text-purple-100 mb-3">
                    Duration (seconds)
                  </label>
                  <input
                    type="number"
                    value={duration}
                    onChange={(e) => setDuration(parseInt(e.target.value))}
                    disabled={isProcessing}
                    min="60"
                    max="600"
                    className="block w-full rounded-md border-gray-300 shadow-sm focus:border-purple-500 focus:ring-purple-500 bg-white/20 text-white border border-white/30"
                  />
                </div>
              </div>

              <div>
                <button
                  type="submit"
                  disabled={!file || isProcessing}
                  className="w-full bg-purple-600 border border-transparent rounded-lg shadow-sm py-3 px-4 text-sm font-semibold text-white hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed transition-colors duration-200"
                >
                  {isProcessing ? 'Generating Podcast...' : 'Generate Podcast'}
                </button>
              </div>
            </form>

            {isProcessing && (
              <div className="mt-6">
                <div className="flex justify-between text-sm font-medium text-purple-100 mb-2">
                  <span>Processing...</span>
                  <span>{Math.round(progress)}%</span>
                </div>
                <div className="w-full bg-gray-700 rounded-full h-2">
                  <div
                    className="bg-gradient-to-r from-purple-500 to-pink-500 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  ></div>
                </div>
              </div>
            )}

            {audioUrl && (
              <div className="mt-8 p-6 bg-white/10 rounded-xl border border-white/20">
                <h3 className="text-lg font-semibold text-white mb-4">
                  Generated Podcast
                </h3>
                <audio controls className="w-full">
                  <source src={audioUrl} type="audio/mpeg" />
                  Your browser does not support the audio element.
                </audio>
                <div className="mt-4 text-sm text-purple-200">
                  <p>Podcast generated successfully!</p>
                </div>
              </div>
            )}
          </div>

          <div className="mt-12 text-center">
            <p className="text-sm text-purple-300">
              Powered by AI • Local processing available • Open source
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default App
```

Now I'll add the required package.json and other frontend configuration files:

frontend/package.json
```json
<<<<<<< SEARCH
