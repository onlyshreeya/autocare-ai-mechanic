
import { useEffect, useRef, useState } from "react";
import {
  Wrench, Send, Paperclip, Image, Mic, Video,
  Bot, User, Plus, History, CalendarDays,
  Activity, X, Loader2, CheckCircle, Car,
  AlertTriangle, Clock, Menu, ChevronRight,
} from "lucide-react";
import "./App.css";

const API = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [history, setHistory] = useState([]);
  const [diagnoses, setDiagnoses] = useState([]);
  const [activeTab, setActiveTab] = useState("chat");
  const [loading, setLoading] = useState(false);
  const [vehicle, setVehicle] = useState("");
  const [media, setMedia] = useState(null);
  const [bookingOpen, setBookingOpen] = useState(false);
  const [bookingSuccess, setBookingSuccess] = useState(false);
  const [createdBookingId, setCreatedBookingId] = useState(null);
  const [booking, setBooking] = useState({
    customer_name: "",
    phone: "",
    vehicle_model: "",
    issue_description: "",
    appointment_date: "",
    appointment_time: "",
  });

  const fileRef = useRef(null);
  const bottomRef = useRef(null);

  useEffect(() => {
    loadHistory();
    loadDiagnoses();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function loadHistory() {
    try {
      const res = await fetch(`${API}/api/chat/`);
      const data = await res.json();
      if (res.ok) {
        const rows = data.history || (Array.isArray(data) ? data : data.results || []);
        setHistory(rows);
      }
    } catch (err) {
      console.error("Chat history:", err);
    }
  }

  function openHistoryItem(item) {
    const formatted = [];
    if (item.user_message || item.message) {
      formatted.push({ role: "user", text: item.user_message || item.message });
    }
    if (item.bot_reply || item.reply) {
      formatted.push({ role: "bot", text: item.bot_reply || item.reply });
    }
    setMessages(formatted);
    setActiveTab("chat");
  }

  async function loadDiagnoses() {
    try {
      const res = await fetch(`${API}/api/diagnosis/`);
      if (!res.ok) return;
      const data = await res.json();
      setDiagnoses(Array.isArray(data) ? data : data.results || []);
    } catch {
      // Diagnosis history endpoint optional handling
    }
  }

  async function sendMessage(e) {
    e?.preventDefault();
    if ((!input.trim() && !media) || loading) return;

    const text = input.trim();
    const selectedMedia = media;
    setInput("");
    setMedia(null);
    setLoading(true);

    const userMessage = {
      role: "user",
      text: text || `Uploaded ${selectedMedia?.name}`,
      file: selectedMedia ? URL.createObjectURL(selectedMedia) : null,
      type: selectedMedia?.type || "",
    };

    setMessages((prev) => [...prev, userMessage]);

    try {
      let uploadedMediaId = null;

      // Step 1: Upload media first if attached
      if (selectedMedia) {
        const form = new FormData();
        form.append("file", selectedMedia);

        const uploadRes = await fetch(`${API}/api/upload/`, {
          method: "POST",
          body: form,
        });

        if (!uploadRes.ok) {
          throw new Error("Media upload failed. Check the backend.");
        }
        const uploadData = await uploadRes.json();
        uploadedMediaId = uploadData.id;
      }

      // Step 2: Send message, history context, and media_id to Chat API
      const res = await fetch(`${API}/api/chat/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message: text,
          media_id: uploadedMediaId,
          history: messages.map((m) => ({ role: m.role, text: m.text })),
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Chat request failed");

      const reply =
        data.bot_reply || data.reply || data.response ||
        "I couldn't generate a response. Please try again.";

      setMessages((prev) => [
        ...prev,
        { role: "bot", text: reply, provider: data.provider },
      ]);

      loadHistory();
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          text: `Error: ${err.message}. Make sure Django server is running.`,
        },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function runDiagnosis() {
    if (!input.trim() || loading) return;

    const symptoms = input.trim();
    setInput("");
    setLoading(true);
    setMessages((prev) => [...prev, { role: "user", text: symptoms }]);

    try {
      const res = await fetch(`${API}/api/diagnosis/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          vehicle_model: vehicle || "Not specified",
          symptoms,
        }),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Diagnosis failed");

      const result =
        data.diagnosis_result || data.result || data.diagnosis ||
        "Diagnosis completed.";

      setMessages((prev) => [
        ...prev,
        {
          role: "bot",
          text: result,
          diagnosis: true,
          severity: data.severity || "unknown",
        },
      ]);

      setDiagnoses((prev) => [data, ...prev]);
      setActiveTab("chat");
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "bot", text: `Diagnosis error: ${err.message}` },
      ]);
    } finally {
      setLoading(false);
    }
  }

  async function submitBooking(e) {
    e.preventDefault();
    try {
      const res = await fetch(`${API}/api/booking/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(booking),
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.error || "Booking failed");

      setCreatedBookingId(data.booking_id);
      setBookingSuccess(true);
      setBookingOpen(false);
      setBooking({
        customer_name: "",
        phone: "",
        vehicle_model: "",
        issue_description: "",
        appointment_date: "",
        appointment_time: "",
      });
    } catch (err) {
      alert(err.message);
    }
  }

  function newChat() {
    setMessages([]);
    setInput("");
    setMedia(null);
    setActiveTab("chat");
  }

  function openBooking() {
    setBooking((prev) => ({
      ...prev,
      vehicle_model: vehicle || prev.vehicle_model,
      issue_description:
        messages.filter((m) => m.role === "user")
          .map((m) => m.text).join("\n"),
    }));
    setBookingOpen(true);
  }

  const latestDiagnosis = [...messages]
    .reverse()
    .find((m) => m.diagnosis);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-icon"><Wrench size={22} /></div>
          <div>
            <h2>Auto<span>Care</span></h2>
            <small>AI MECHANIC</small>
          </div>
        </div>

        <button className="new-chat" onClick={newChat}>
          <Plus size={18} /> New conversation
        </button>

        <p className="nav-label">WORKSPACE</p>
        <button
          className={`nav-item ${activeTab === "chat" ? "active" : ""}`}
          onClick={() => setActiveTab("chat")}
        >
          <Bot size={18} /> AI Mechanic
        </button>
        <button
          className={`nav-item ${activeTab === "history" ? "active" : ""}`}
          onClick={() => setActiveTab("history")}
        >
          <History size={18} /> Chat history
        </button>
        <button
          className={`nav-item ${activeTab === "diagnoses" ? "active" : ""}`}
          onClick={() => setActiveTab("diagnoses")}
        >
          <Activity size={18} /> Diagnoses
        </button>

        <div className="sidebar-bottom">
          <div className="status-dot" />
          <div>
            <strong>AI System Online</strong>
            <small>Ready to assist</small>
          </div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div className="topbar-title">
            <span className="mobile-brand"><Wrench size={20} /></span>
            <div>
              <h3>
                {activeTab === "chat" ? "AI Mechanic" :
                  activeTab === "history" ? "Chat History" : "Diagnosis History"}
              </h3>
              <p>Your personal automotive assistant</p>
            </div>
          </div>
          <div className="online-badge"><span /> AI ONLINE</div>
        </header>
        {bookingSuccess && (
          <div className="booking-success-overlay">
            <div className="booking-success-modal">
              <div className="success-icon">✓</div>

              <h2>Booking Confirmed!</h2>

              <p>
                Your mechanic appointment has been
                submitted successfully.
              </p>

              <p className="success-details">
                {booking.appointment_date} at {booking.appointment_time}
              </p>

              <button
                onClick={() => {
                  setBookingSuccess(false);
                  setBookingOpen(false);
                }}
              >
                Done
              </button>
            </div>
          </div>
        )}
        {activeTab === "chat" && (
          <section className="chat-layout">
            <div className="chat-scroll">
              {messages.length === 0 ? (
                <div className="welcome">
                  <div className="welcome-icon"><Car size={30} /></div>
                  <span className="eyebrow">YOUR AI CAR EXPERT</span>
                  <h1>What's going on<br />with your <span>car?</span></h1>
                  <p>Describe the issue, share a photo or video, and get help understanding what might be wrong.</p>

                  <div className="suggestions">
                    {[
                      "My car engine is overheating",
                      "My car won't start",
                      "I hear a noise when braking",
                    ].map((s) => (
                      <button key={s} onClick={() => setInput(s)}>
                        <Wrench size={15} /> {s} <ChevronRight size={15} />
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="messages">
                  {messages.map((m, i) => (
                    <div className={`message ${m.role === "user" ? "user" : "bot"}`} key={i}>
                      <div className="avatar">
                        {m.role === "bot" ? <Bot size={17} /> : <User size={17} />}
                      </div>
                      <div className="message-content">
                        <div className="message-name">
                          {m.role === "bot" ? "AutoCare AI" : "You"}
                          {m.diagnosis && <span className="diagnosis-tag">DIAGNOSIS</span>}
                        </div>
                        <div className="bubble">
                          {m.file && (
                            m.type.startsWith("image/") ?
                              <img src={m.file} className="chat-image" alt="Upload" /> :
                              <div className="file-preview"><Paperclip size={15} /> Attachment</div>
                          )}
                          {m.text}
                        </div>
                        {m.diagnosis && (
                          <div className="diagnosis-actions">
                            <span className="severity">
                              <AlertTriangle size={14} /> {m.severity}
                            </span>
                            <button onClick={openBooking}>
                              <CalendarDays size={15} /> Book Mechanic
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                  {loading && (
                    <div className="message bot">
                      <div className="avatar"><Bot size={17} /></div>
                      <div className="message-content">
                        <div className="bubble loading"><Loader2 size={16} className="spin" /> Thinking...</div>
                      </div>
                    </div>
                  )}
                  <div ref={bottomRef} />
                </div>
              )}
            </div>

            <div className="composer-wrap">
              <div className="vehicle-row">
                <Car size={15} />
                <input
                  value={vehicle}
                  onChange={(e) => setVehicle(e.target.value)}
                  placeholder="Vehicle model (e.g. Honda City)"
                />
                <span>OPTIONAL</span>
              </div>

              {media && (
                <div className="attached-file">
                  <Paperclip size={15} /> {media.name}
                  <button onClick={() => setMedia(null)}><X size={15} /></button>
                </div>
              )}

              <form className="composer" onSubmit={sendMessage}>
                <textarea
                  rows={2}
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Describe your car problem..."
                  onKeyDown={(e) => {
                    if (e.key === "Enter" && !e.shiftKey) {
                      e.preventDefault();
                      sendMessage();
                    }
                  }}
                />
                <div className="composer-bottom">
                  <div className="composer-tools">
                    <button type="button" title="Attach image, audio or video" onClick={() => fileRef.current?.click()}>
                      <Paperclip size={17} />
                    </button>
                    <span>Image · Audio · Video</span>
                    <input
                      ref={fileRef}
                      type="file"
                      accept="image/*,audio/*,video/*"
                      hidden
                      onChange={(e) => setMedia(e.target.files?.[0] || null)}
                    />
                  </div>
                  <div className="send-actions">
                    <button type="button" className="diagnose-btn" onClick={runDiagnosis} disabled={!input.trim() || loading}>
                      <Activity size={15} /> Diagnose
                    </button>
                    <button className="send-btn" type="submit" disabled={loading || (!input.trim() && !media)}>
                      {loading ? <Loader2 size={17} className="spin" /> : <Send size={17} />}
                    </button>
                  </div>
                </div>
              </form>
              <p className="disclaimer">AI suggestions are informational and don't replace a professional mechanic's inspection.</p>
            </div>
          </section>
        )}

        {activeTab === "history" && (
          <section className="data-page">
            <h2>Previous conversations</h2>
            <p>Your saved chat messages from the backend. Click any conversation to view it in chat.</p>
            {history.length === 0 ? <div className="empty-state">No chat history found yet.</div> :
              history.map((item, i) => (
                <div className="data-card clickable" key={item.id || i} onClick={() => openHistoryItem(item)} style={{ cursor: "pointer" }}>
                  <History size={18} />
                  <div>
                    <strong>{item.user_message || item.message || "Conversation"}</strong>
                    <p>{item.bot_reply || item.reply || ""}</p>
                    <small>{item.created_at ? new Date(item.created_at).toLocaleString() : ""}</small>
                  </div>
                </div>
              ))}
          </section>
        )}

        {activeTab === "diagnoses" && (
          <section className="data-page">
            <h2>Diagnosis history</h2>
            <p>Previously recorded vehicle diagnoses.</p>
            {diagnoses.length === 0 ? <div className="empty-state">No diagnosis history found yet.</div> :
              diagnoses.map((item, i) => (
                <div className="data-card" key={item.id || i}>
                  <Activity size={18} />
                  <div>
                    <strong>{item.vehicle_model || "Vehicle"}</strong>
                    <p>{item.symptoms}</p>
                    <p>{item.diagnosis_result || item.result || ""}</p>
                    <small>{item.severity || "Severity not specified"}</small>
                  </div>
                </div>
              ))}
          </section>
        )}
      </main>

      {bookingOpen && (
        <div className="modal-backdrop" onClick={() => setBookingOpen(false)}>
          <div className="booking-modal" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setBookingOpen(false)}><X /></button>
            <div className="modal-icon"><CalendarDays size={23} /></div>
            <span className="eyebrow">MECHANIC APPOINTMENT</span>
            <h2>Book a mechanic</h2>
            <p>Choose a convenient date and time for your vehicle inspection.</p>

            <form onSubmit={submitBooking}>
              <label>Full name</label>
              <input required value={booking.customer_name} onChange={(e) => setBooking({ ...booking, customer_name: e.target.value })} placeholder="Your name" />
              <label>Phone number</label>
              <input required type="tel" value={booking.phone} onChange={(e) => setBooking({ ...booking, phone: e.target.value })} placeholder="10-digit phone number" />
              <label>Vehicle model</label>
              <input required value={booking.vehicle_model} onChange={(e) => setBooking({ ...booking, vehicle_model: e.target.value })} placeholder="e.g. Honda City" />
              <label>Issue description</label>
              <textarea required rows={2} value={booking.issue_description} onChange={(e) => setBooking({ ...booking, issue_description: e.target.value })} placeholder="Describe the issue" />
              <div className="form-row">
                <div><label>Date</label><input required type="date" min={new Date().toISOString().split("T")[0]} value={booking.appointment_date} onChange={(e) => setBooking({ ...booking, appointment_date: e.target.value })} /></div>
                <div>
                  <label>Time Slot</label>

                  <select
                    required
                    value={booking.appointment_time}
                    onChange={(e) =>
                      setBooking({ ...booking, appointment_time: e.target.value })
                    }
                  >
                    <option value="">Choose a time slot</option>
                    <option value="09:00">09:00 AM</option>
                    <option value="10:00">10:00 AM</option>
                    <option value="11:00">11:00 AM</option>
                    <option value="12:00">12:00 PM</option>
                    <option value="13:00">01:00 PM</option>
                    <option value="14:00">02:00 PM</option>
                    <option value="15:00">03:00 PM</option>
                    <option value="16:00">04:00 PM</option>
                    <option value="17:00">05:00 PM</option>
                  </select>
                </div>
              </div>
              <button className="submit-booking" type="submit"><CalendarDays size={17} /> Confirm booking</button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}