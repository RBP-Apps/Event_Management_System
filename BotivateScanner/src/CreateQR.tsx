import { useState } from "react"
import { QrCode, Download, Copy, Check } from "lucide-react"
import QRCodeLib from "qrcode"

export function CreateQR() {
  const [formData, setFormData] = useState({
    name: "",
    phone: "",
    email: "",
    company: ""
  })
  const [loading, setLoading] = useState(false)
  const [qrData, setQrData] = useState<{ qrId: string; qrUrl: string; qrImage?: string } | null>(null)
  const [copied, setCopied] = useState(false)

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const generateQR = async () => {
    if (!formData.name || !formData.phone || !formData.email || !formData.company) {
      alert("Please fill all fields")
      return
    }

    setLoading(true)
    try {
      const response = await fetch("/create-qr", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(formData)
      })

      const res = await response.json()
      if (res.success) {
        const qrImage = await QRCodeLib.toDataURL(res.qrUrl, {
          errorCorrectionLevel: "H",
          type: "image/png",
          width: 300,
          margin: 2
        })
        setQrData({ qrId: res.qrId, qrUrl: res.qrUrl, qrImage })
      } else {
        alert("Failed to create QR: " + res.message)
      }
    } catch (err) {
      console.error(err)
      alert("Error creating QR")
    } finally {
      setLoading(false)
    }
  }

  const downloadQR = async () => {
    if (!qrData?.qrImage) return
    const link = document.createElement("a")
    link.href = qrData.qrImage
    link.download = `${formData.name.replace(/\s+/g, "_")}_QR.png`
    link.click()
  }

  const copyLink = () => {
    navigator.clipboard.writeText(qrData?.qrUrl || "")
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 p-4 sm:p-6 lg:p-8 font-sans">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="inline-flex items-center justify-center p-4 bg-blue-600 text-white rounded-3xl shadow-xl mb-6">
            <QrCode className="w-8 h-8" />
          </div>
          <h1 className="text-4xl font-black text-slate-800 tracking-tight">Create Your QR</h1>
          <p className="text-slate-500 text-lg mt-3">Share your profile instantly with anyone</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Form Section */}
          <div className="bg-white rounded-[2.5rem] shadow-2xl p-8 border border-white/50">
            <h2 className="text-2xl font-black text-slate-800 mb-8">Your Details</h2>

            <div className="space-y-5">
              <div>
                <label className="text-[11px] font-black uppercase tracking-widest text-slate-500 ml-1 block mb-2">
                  Full Name
                </label>
                <input
                  type="text"
                  name="name"
                  placeholder="Ex: Rajesh Kumar"
                  value={formData.name}
                  onChange={handleInputChange}
                  className="w-full px-5 py-3.5 bg-slate-50 border border-slate-100 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none text-slate-700 font-semibold"
                />
              </div>

              <div>
                <label className="text-[11px] font-black uppercase tracking-widest text-slate-500 ml-1 block mb-2">
                  Phone Number
                </label>
                <input
                  type="tel"
                  name="phone"
                  placeholder="+91 9999999999"
                  value={formData.phone}
                  onChange={handleInputChange}
                  className="w-full px-5 py-3.5 bg-slate-50 border border-slate-100 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none text-slate-700 font-semibold"
                />
              </div>

              <div>
                <label className="text-[11px] font-black uppercase tracking-widest text-slate-500 ml-1 block mb-2">
                  Email Address
                </label>
                <input
                  type="email"
                  name="email"
                  placeholder="rajesh@company.com"
                  value={formData.email}
                  onChange={handleInputChange}
                  className="w-full px-5 py-3.5 bg-slate-50 border border-slate-100 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none text-slate-700 font-semibold"
                />
              </div>

              <div>
                <label className="text-[11px] font-black uppercase tracking-widest text-slate-500 ml-1 block mb-2">
                  Company / Organization
                </label>
                <input
                  type="text"
                  name="company"
                  placeholder="ABC Pvt Ltd"
                  value={formData.company}
                  onChange={handleInputChange}
                  className="w-full px-5 py-3.5 bg-slate-50 border border-slate-100 rounded-2xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none text-slate-700 font-semibold"
                />
              </div>

              <button
                onClick={generateQR}
                disabled={loading}
                className="w-full bg-blue-600 text-white font-black py-4 rounded-2xl shadow-xl flex items-center justify-center gap-3 transition-all active:scale-95 hover:bg-blue-700 disabled:opacity-70 mt-6"
              >
                {loading ? "Generating..." : <><QrCode className="w-5 h-5" /> GENERATE MY QR</>}
              </button>
            </div>
          </div>

          {/* QR Display Section */}
          <div className="bg-white rounded-[2.5rem] shadow-2xl p-8 border border-white/50">
            {qrData ? (
              <div className="text-center space-y-6">
                <h2 className="text-2xl font-black text-slate-800">Your QR Code Ready!</h2>

                {/* QR Code Display */}
                <div className="bg-slate-50 p-6 rounded-2xl border border-slate-100 inline-block">
                  <img
                    src={qrData.qrImage}
                    alt="Your QR Code"
                    className="w-72 h-72 rounded-lg"
                  />
                </div>

                {/* Profile Info */}
                <div className="bg-blue-50 rounded-2xl p-5 text-left border border-blue-100">
                  <p className="text-sm text-slate-600">
                    <span className="font-black text-blue-600">Profile:</span> {formData.name}
                  </p>
                  <p className="text-sm text-slate-600 mt-1">
                    <span className="font-black text-blue-600">Company:</span> {formData.company}
                  </p>
                  <p className="text-[12px] text-slate-500 mt-2 break-all">
                    <span className="font-black text-blue-600">Link:</span> {qrData.qrUrl}
                  </p>
                </div>

                {/* Action Buttons */}
                <div className="flex flex-col gap-3">
                  <button
                    onClick={downloadQR}
                    className="w-full bg-slate-900 text-white font-black py-3 rounded-2xl shadow-xl flex items-center justify-center gap-2 transition-all active:scale-95 hover:bg-black"
                  >
                    <Download className="w-5 h-5" /> DOWNLOAD QR
                  </button>

                  <button
                    onClick={copyLink}
                    className="w-full bg-blue-600 text-white font-black py-3 rounded-2xl shadow-xl flex items-center justify-center gap-2 transition-all active:scale-95 hover:bg-blue-700"
                  >
                    {copied ? <><Check className="w-5 h-5" /> COPIED!</> : <><Copy className="w-5 h-5" /> COPY LINK</>}
                  </button>
                </div>

                <div className="text-[12px] text-slate-500 text-center italic">
                  Share the QR code or link with anyone to let them view your profile instantly!
                </div>
              </div>
            ) : (
              <div className="h-full flex items-center justify-center text-center">
                <div className="space-y-4">
                  <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto">
                    <QrCode className="w-10 h-10 text-blue-600" />
                  </div>
                  <p className="text-slate-500 font-semibold">Fill in your details and generate your unique QR code</p>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

export default CreateQR
