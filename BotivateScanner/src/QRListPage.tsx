import { useState, useEffect } from "react"
import { Home, QrCode, Calendar, ArrowRight, Loader, Pencil, X, Check } from "lucide-react"

interface QRProfile {
  Name: string
  Phone: string
  Email: string
  Company: string
  QR_ID: string
  "Created Date": string | Date
}

export function QRListPage({ onBack, onSelectQR }: { onBack: () => void; onSelectQR: (qrId: string) => void }) {
  const [profiles, setProfiles] = useState<QRProfile[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [editingId, setEditingId] = useState<string | null>(null)
  const [editForm, setEditForm] = useState({ name: "", phone: "", email: "", company: "" })
  const [saving, setSaving] = useState(false)

  const APPS_SCRIPT_URL = "https://script.google.com/macros/s/AKfycbzCPeTYr3DyfmQaEJCQ_A7KnKJ9gZtz4zO-chHkLyvxMFsCd2JRWikUB8LxpFwwbuczxw/exec"

  useEffect(() => {
    fetchQRProfiles()
  }, [])

  const fetchQRProfiles = async () => {
    try {
      setLoading(true)
      setError(null)

      // Try backend first (easier to debug)
      try {
        const backendResponse = await fetch("/get-all-qr-profiles")
        if (backendResponse.ok) {
          const res = await backendResponse.json()
          if (res.success && res.data) {
            const sortedData = (res.data as QRProfile[]).sort((a, b) => {
              const dateA = new Date(a["Created Date"]).getTime()
              const dateB = new Date(b["Created Date"]).getTime()
              return dateB - dateA
            })
            setProfiles(sortedData)
            setLoading(false)
            return
          }
        }
      } catch (e) {
        console.log("Backend endpoint not available, trying Apps Script")
      }

      // Fallback to Apps Script
      const response = await fetch(APPS_SCRIPT_URL, {
        method: 'POST',
        body: JSON.stringify({ action: 'get_all_qr_profiles' }),
        headers: { "Content-Type": "text/plain;charset=utf-8" }
      })
      const res = await response.json()
      if (res.success && res.data) {
        const sortedData = (res.data as QRProfile[]).sort((a, b) => {
          const dateA = new Date(a["Created Date"]).getTime()
          const dateB = new Date(b["Created Date"]).getTime()
          return dateB - dateA
        })
        setProfiles(sortedData)
      } else {
        setError(res.message || "Failed to fetch QR profiles. Make sure you have created some QR profiles first.")
      }
    } catch (err) {
      console.error(err)
      setError("Error loading QR profiles. Check console for details.")
    } finally {
      setLoading(false)
    }
  }

  const formatDate = (dateStr: string | Date) => {
    try {
      const date = new Date(dateStr)
      return date.toLocaleDateString('en-IN', { day: '2-digit', month: 'short', year: 'numeric' })
    } catch {
      return String(dateStr)
    }
  }

  const startEdit = (e: React.MouseEvent, profile: QRProfile) => {
    e.stopPropagation()
    setEditingId(profile.QR_ID)
    setEditForm({
      name: profile.Name || "",
      phone: profile.Phone || "",
      email: profile.Email || "",
      company: profile.Company || ""
    })
  }

  const cancelEdit = (e: React.MouseEvent) => {
    e.stopPropagation()
    setEditingId(null)
  }

  const saveEdit = async (e: React.MouseEvent, qrId: string) => {
    e.stopPropagation()
    setSaving(true)
    try {
      const response = await fetch(`/update-qr/${qrId}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(editForm)
      })
      const res = await response.json()
      if (res.success) {
        setProfiles(prev => prev.map(p =>
          p.QR_ID === qrId
            ? { ...p, Name: editForm.name, Phone: editForm.phone, Email: editForm.email, Company: editForm.company }
            : p
        ))
        setEditingId(null)
      } else {
        alert("Failed to update: " + (res.message || "Unknown error"))
      }
    } catch (err) {
      console.error(err)
      alert("Error updating profile. Try again.")
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 p-4 sm:p-6 lg:p-8 font-sans">
      {/* Header with Back Button */}
      <div className="flex items-center justify-between mb-8">
        <button
          onClick={onBack}
          className="bg-white text-slate-800 font-black px-6 py-3 rounded-2xl shadow-xl flex items-center gap-2 hover:bg-slate-50 transition-all"
        >
          <Home className="w-5 h-5" /> BACK
        </button>
        <h1 className="text-3xl font-black text-slate-800">QR Profiles</h1>
        <div className="w-32" /> {/* Spacer for centering */}
      </div>

      <div className="max-w-4xl mx-auto">
        {/* Loading State */}
        {loading && (
          <div className="text-center py-20">
            <div className="inline-flex items-center justify-center">
              <Loader className="w-8 h-8 text-blue-600 animate-spin" />
            </div>
            <p className="text-slate-500 font-semibold mt-4">Loading QR profiles...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-red-50 border-2 border-red-200 rounded-2xl p-6 text-center">
            <p className="text-red-600 font-black">{error}</p>
            <button
              onClick={fetchQRProfiles}
              className="mt-4 bg-red-600 text-white font-black px-6 py-2 rounded-xl hover:bg-red-700 transition-all"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && profiles.length === 0 && (
          <div className="text-center py-20">
            <div className="w-20 h-20 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-6">
              <QrCode className="w-10 h-10 text-blue-600" />
            </div>
            <h2 className="text-2xl font-black text-slate-800 mb-2">No QR Profiles Yet</h2>
            <p className="text-slate-500 font-semibold">Create your first QR profile to see it here</p>
          </div>
        )}

        {/* Profiles Grid */}
        {!loading && !error && profiles.length > 0 && (
          <div className="space-y-4">
            <div className="text-slate-600 font-black text-sm uppercase tracking-wide mb-6">
              {profiles.length} Profile{profiles.length !== 1 ? 's' : ''} Created
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {profiles.map((profile) => (
                editingId === profile.QR_ID ? (
                  <div
                    key={profile.QR_ID}
                    className="bg-white rounded-2xl shadow-lg border-2 border-blue-300 p-6 text-left"
                  >
                    <div className="space-y-3">
                      <input
                        type="text"
                        placeholder="Full Name"
                        value={editForm.name}
                        onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                        className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-slate-700 font-semibold text-sm"
                      />
                      <input
                        type="text"
                        placeholder="Company"
                        value={editForm.company}
                        onChange={(e) => setEditForm({ ...editForm, company: e.target.value })}
                        className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-slate-700 font-semibold text-sm"
                      />
                      <input
                        type="tel"
                        placeholder="Phone"
                        value={editForm.phone}
                        onChange={(e) => setEditForm({ ...editForm, phone: e.target.value })}
                        className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-slate-700 font-semibold text-sm"
                      />
                      <input
                        type="email"
                        placeholder="Email"
                        value={editForm.email}
                        onChange={(e) => setEditForm({ ...editForm, email: e.target.value })}
                        className="w-full px-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none text-slate-700 font-semibold text-sm"
                      />
                      <div className="flex gap-2 pt-1">
                        <button
                          onClick={(e) => saveEdit(e, profile.QR_ID)}
                          disabled={saving}
                          className="flex-1 bg-blue-600 text-white font-black py-2.5 rounded-xl shadow-md flex items-center justify-center gap-2 hover:bg-blue-700 transition-all disabled:opacity-60 text-sm"
                        >
                          <Check className="w-4 h-4" /> {saving ? "Saving..." : "Save"}
                        </button>
                        <button
                          onClick={cancelEdit}
                          disabled={saving}
                          className="flex-1 bg-slate-100 text-slate-600 font-black py-2.5 rounded-xl flex items-center justify-center gap-2 hover:bg-slate-200 transition-all text-sm"
                        >
                          <X className="w-4 h-4" /> Cancel
                        </button>
                      </div>
                    </div>
                  </div>
                ) : (
                  <button
                    key={profile.QR_ID}
                    onClick={() => onSelectQR(profile.QR_ID)}
                    className="bg-white rounded-2xl shadow-lg border-2 border-slate-100 p-6 text-left hover:shadow-xl hover:border-blue-300 transition-all group relative"
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1 min-w-0">
                        <h3 className="text-xl font-black text-slate-800 truncate group-hover:text-blue-600 transition-all">
                          {profile.Name}
                        </h3>
                        <p className="text-sm text-slate-500 font-semibold mt-1">
                          {profile.Company}
                        </p>
                        <p className="text-[12px] text-slate-400 mt-2 flex items-center gap-1">
                          <Calendar className="w-3 h-3" />
                          {formatDate(profile["Created Date"])}
                        </p>
                        <p className="text-[12px] text-slate-400 mt-1">
                          📞 {profile.Phone}
                        </p>
                      </div>
                      <div className="flex-shrink-0 flex items-center gap-2">
                        <span
                          role="button"
                          onClick={(e) => startEdit(e, profile)}
                          className="bg-slate-100 text-slate-500 w-9 h-9 rounded-full flex items-center justify-center hover:bg-slate-200 hover:text-slate-700 transition-all"
                          title="Edit profile"
                        >
                          <Pencil className="w-4 h-4" />
                        </span>
                        <div className="bg-blue-100 text-blue-600 w-10 h-10 rounded-full flex items-center justify-center group-hover:bg-blue-600 group-hover:text-white transition-all">
                          <ArrowRight className="w-5 h-5" />
                        </div>
                      </div>
                    </div>
                  </button>
                )
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default QRListPage
