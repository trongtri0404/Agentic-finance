import React, { useState, useRef, useEffect } from "react";
import { Send, BarChart2, Building2, FileText, Bot, User } from "lucide-react";

// Ticker Data (Mock)
const TICKER_DATA = [
  { symbol: "MSFT", price: "$420.75", change: "+0.8%" },
  { symbol: "BA", price: "$185.25", change: "-0.3%" },
  { symbol: "KO", price: "$61.45", change: "+0.5%" },
  { symbol: "JPM", price: "$198.32", change: "+1.1%" },
  { symbol: "V", price: "$282.10", change: "+0.6%" },
  { symbol: "UNH", price: "$527.80", change: "-0.4%" },
  { symbol: "HD", price: "$345.60", change: "+0.9%" },
  { symbol: "AMGN", price: "$298.45", change: "+0.3%" },
  { symbol: "GS", price: "$412.30", change: "+1.5%" },
  { symbol: "AAPL", price: "$170.08", change: "+1.2%" },
];

function App() {
  const [question, setQuestion] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  async function askAgent() {
    if (!question.trim()) return;

    const currentQuestion = question.trim();
    setLoading(true);

    const userMessage = {
      id: Date.now().toString(),
      role: "user",
      text: currentQuestion
    };

    setMessages((prev) => [...prev, userMessage]);
    setQuestion("");

    try {
      const apiUrl = import.meta.env.VITE_API_URL 
        ? `${import.meta.env.VITE_API_URL}/chat` 
        : "http://localhost:8000/chat";

      const res = await fetch(apiUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: currentQuestion })
      });

      if (!res.ok) throw new Error(`HTTP Error: ${res.status}`);

      const data = await res.json();
      
      const agentMessage = {
        id: (Date.now() + 1).toString(),
        role: "agent",
        text: data.answer || "Không có câu trả lời từ hệ thống.",
        route: data.route || "unknown"
      };

      setMessages((prev) => [...prev, agentMessage]);
    } catch (err) {
      const errorMessage = {
        id: (Date.now() + 2).toString(),
        role: "agent",
        isError: true,
        text: "Hệ thống đang gặp sự cố kết nối. Vui lòng kiểm tra lại backend (FastAPI).",
        route: "error"
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }

  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      askAgent();
    }
  };

  const hasStartedChat = messages.length > 0;

  return (
    <div style={{ display: "flex", flexDirection: "column", height: "100vh", width: "100%", position: "relative" }}>
      
      {/* 1. HEADER */}
      <header style={{ 
        padding: "16px 32px", 
        display: "flex", 
        justifyContent: "space-between", 
        alignItems: "center" 
      }}>
        {/* Logo & Title */}
        <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
          <div style={{
            background: "#0ea5e9", // Light blue matching mockup
            color: "white",
            fontWeight: "bold",
            fontSize: "20px",
            width: "48px",
            height: "48px",
            borderRadius: "12px",
            display: "flex",
            alignItems: "center",
            justifyContent: "center"
          }}>
            DJ
          </div>
          <div style={{ display: "flex", flexDirection: "column" }}>
            <h1 style={{ fontSize: "1.1rem", margin: 0, fontWeight: 600 }}>DJIA Financial Agent</h1>
            <span style={{ fontSize: "0.65rem", color: "var(--text-muted)", letterSpacing: "1px" }}>POWERED BY GEMINI AI</span>
          </div>
        </div>

        {/* Badges */}
        <div style={{ display: "flex", gap: "12px" }}>
          {['SQL', 'RAG', 'Gemini'].map(badge => (
            <div key={badge} style={{
              background: "rgba(255,255,255,0.05)",
              border: "1px solid var(--border-light)",
              padding: "6px 12px",
              borderRadius: "20px",
              fontSize: "0.75rem",
              color: "var(--text-secondary)",
              display: "flex",
              alignItems: "center",
              gap: "6px"
            }}>
              <span className="status-dot"></span>
              {badge}
            </div>
          ))}
        </div>
      </header>

      {/* 2. TICKER */}
      <div className="ticker-wrap">
        <div className="ticker-content">
          {[...TICKER_DATA, ...TICKER_DATA].map((stock, i) => {
            const isPositive = stock.change.startsWith('+');
            return (
              <div key={i} className="stock-item">
                <span className="stock-symbol">{stock.symbol}</span>
                <span className="stock-price">{stock.price}</span>
                <span className={`stock-change ${isPositive ? 'positive' : 'negative'}`}>
                  {stock.change}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* 3. MAIN CONTENT */}
      <main style={{
        flex: 1,
        overflowY: "auto",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        padding: "24px",
      }}>
        {!hasStartedChat ? (
          /* Welcome Screen */
          <div style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            height: "100%",
            maxWidth: "800px",
            width: "100%",
            gap: "24px"
          }}>
            {/* Big Chart Icon (Using an emoji/div to match mockup as close as possible) */}
            <div style={{
              background: "linear-gradient(to bottom, #f1f5f9, #cbd5e1)",
              width: "72px",
              height: "72px",
              borderRadius: "16px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              fontSize: "36px",
              boxShadow: "0 10px 25px rgba(0,0,0,0.5)"
            }}>
              📈
            </div>
            
            <div style={{ textAlign: "center" }}>
              <h2 style={{ 
                fontSize: "2rem", 
                fontWeight: 600, 
                color: "var(--accent-teal)",
                marginBottom: "12px"
              }}>
                DJIA Financial Agent
              </h2>
              <p style={{ color: "var(--text-secondary)", fontSize: "0.95rem", lineHeight: 1.6, maxWidth: "500px", margin: "0 auto" }}>
                Hỏi bất kỳ câu hỏi nào về 30 công ty trong chỉ số Dow Jones. Agent sẽ tự động chọn SQL hoặc RAG để trả lời chính xác nhất.
              </p>
            </div>

            {/* 3 Cards */}
            <div style={{ 
              display: "flex", 
              gap: "20px", 
              marginTop: "32px",
              width: "100%",
              justifyContent: "center"
            }}>
              {[
                { icon: <BarChart2 size={24} color="#60a5fa" />, title: "Giá cổ phiếu", desc: "Truy vấn giá đóng/mở cửa" },
                { icon: <Building2 size={24} color="#a78bfa" />, title: "Thông tin công ty", desc: "Sector, industry, mô tả" },
                { icon: <FileText size={24} color="#f472b6" />, title: "Báo cáo thường niên", desc: "RAG tìm kiếm tài liệu" },
              ].map((card, idx) => (
                <div key={idx} style={{
                  background: "var(--bg-card)",
                  borderRadius: "16px",
                  padding: "20px",
                  width: "220px",
                  border: "1px solid var(--border-light)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "12px"
                }}>
                  <div style={{
                    background: "rgba(0,0,0,0.2)",
                    width: "40px",
                    height: "40px",
                    borderRadius: "8px",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center"
                  }}>
                    {card.icon}
                  </div>
                  <div>
                    <h3 style={{ fontSize: "0.95rem", margin: "0 0 4px 0", color: "var(--text-primary)" }}>{card.title}</h3>
                    <p style={{ fontSize: "0.75rem", margin: 0, color: "var(--text-muted)" }}>{card.desc}</p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        ) : (
          /* Chat Screen */
          <div style={{ maxWidth: "800px", width: "100%", display: "flex", flexDirection: "column", gap: "24px" }}>
            {messages.map((m) => {
              const isUser = m.role === "user";
              return (
                <div key={m.id} style={{
                  display: "flex",
                  gap: "16px",
                  flexDirection: isUser ? "row-reverse" : "row",
                  alignItems: "flex-start"
                }}>
                  <div style={{
                    width: "36px", height: "36px", borderRadius: "50%",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    background: isUser ? "var(--bg-card)" : "rgba(16, 185, 129, 0.1)",
                    border: `1px solid ${isUser ? "var(--border-light)" : "var(--border-accent)"}`,
                    color: isUser ? "white" : "var(--accent-teal)",
                    flexShrink: 0,
                    marginTop: "4px"
                  }}>
                    {isUser ? <User size={18} /> : <Bot size={18} />}
                  </div>
                  <div style={{
                    maxWidth: "85%",
                    padding: "16px",
                    borderRadius: "16px",
                    background: isUser ? "var(--bg-card)" : "transparent",
                    border: isUser ? "1px solid var(--border-light)" : "none",
                    color: m.isError ? "var(--stock-red)" : "var(--text-primary)",
                    lineHeight: "1.6",
                    fontSize: "0.95rem"
                  }}>
                    {m.text.split('\n').map((item, key) => <React.Fragment key={key}>{item}<br/></React.Fragment>)}
                    {m.route && m.route !== "greeting" && !m.isError && (
                      <div style={{
                        marginTop: "12px", fontSize: "0.7rem", color: "var(--text-secondary)",
                        background: "rgba(255,255,255,0.05)", display: "inline-block",
                        padding: "4px 8px", borderRadius: "8px", border: "1px solid var(--border-light)"
                      }}>
                        Route: {m.route.toUpperCase()}
                      </div>
                    )}
                  </div>
                </div>
              );
            })}
            
            {loading && (
               <div style={{ display: "flex", gap: "16px", alignItems: "center" }}>
                  <div style={{
                    width: "36px", height: "36px", borderRadius: "50%",
                    display: "flex", alignItems: "center", justifyContent: "center",
                    background: "rgba(16, 185, 129, 0.1)",
                    border: "1px solid var(--border-accent)",
                    color: "var(--accent-teal)"
                  }}>
                    <Bot size={18} />
                  </div>
                  <div style={{ color: "var(--text-secondary)", fontSize: "0.9rem" }}>Đang xử lý...</div>
               </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </main>

      {/* 4. INPUT AREA */}
      <footer style={{
        padding: "24px",
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        width: "100%"
      }}>
        <div style={{
          position: "relative",
          width: "100%",
          maxWidth: "800px",
          display: "flex",
          alignItems: "center"
        }}>
          <input
            ref={inputRef}
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={loading}
            placeholder="Hỏi về cổ phiếu, công ty, hoặc báo cáo tài chính..."
            style={{
              width: "100%",
              padding: "16px 60px 16px 24px",
              borderRadius: "30px", // Pill shape
              background: "var(--bg-input)",
              border: "1px solid var(--border-light)",
              color: "white",
              fontSize: "0.95rem"
            }}
          />
          <button
            onClick={askAgent}
            disabled={loading || !question.trim()}
            style={{
              position: "absolute",
              right: "8px",
              background: (loading || !question.trim()) ? "rgba(255,255,255,0.1)" : "var(--accent-teal)",
              color: "white",
              borderRadius: "50%",
              width: "40px",
              height: "40px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center"
            }}
          >
            <Send size={18} style={{ marginLeft: "2px" }} />
          </button>
        </div>
        
        <div style={{ marginTop: "12px", fontSize: "0.7rem", color: "var(--text-muted)" }}>
          Hỗ trợ 30 công ty DJIA - SQL + RAG + Gemini AI
        </div>
      </footer>

    </div>
  );
}

export default App;