require("dotenv").config()
const express = require("express")
const mysql = require("mysql2/promise")
const cors = require("cors")
const path = require("path")
const app = express()

app.use(cors())
app.use(express.json())
app.use(express.static(path.join(__dirname, "web")))

const currentDatabase = process.env.DB_NAME

const db = mysql.createPool({
  host: process.env.DB_HOST,
  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD,
  database: currentDatabase,
  port: process.env.DB_PORT,
  waitForConnections: true,
  connectionLimit: 10,
  multipleStatements: true,
  charset: 'utf8mb4'
})

app.use((err, req, res, next) => {
    console.error(err);

    const status = err.status || 500;

    const messages = {
        400: { Message: "ส่งข้อมูลมาไม่ถูก pattern", code: 400 },
        404: { Message: "ไม่รู้จัก Route ที่เรียกใช้ครับ", code: 404 },
        405: { Message: "Method ไม่ถูกต้องครับ", Status: 405 },
        500: { Message: "Internal Server Error", Status: 500 },
        502: { Message: "Bad Gateway", Status: 502 },
        503: { Message: "Service Unavailable", Status: 503 },
        504: { Message: "Gateway Timeout", Status: 504 }
    };

    res.status(status).json(messages[status] || messages[500]);
});

app.get("/health", async (req, res) => {
  res.status(200).json({ status: "Online" })
})

app.post("/log", async (req, res) => {
  const { id_mongo, id_snake, confi, snake_found, confidence } = req.body
  const conn = await db.getConnection()
  try {
    await conn.query(`USE ${currentDatabase}`)
    
    if (id_mongo && (id_snake || snake_found)) {
      await conn.query(
        "INSERT INTO feedback_log (id_mongo, id_snake, confi, time) VALUES (?, ?, ?, NOW())",
        [id_mongo, id_snake || snake_found, confi || confidence]
      )
      return res.json({ result: "Logged to feedback_log successfully" })
    }
    res.status(400).json({ error: "Missing required fields" })
  } catch (err) {
    res.status(500).json({ error: err.message })
  } finally {
    conn.release()
  }
})

app.post("/feedback", async (req, res) => {
  const { id_mongo, feedback } = req.body
  if (!id_mongo || !feedback) {
    return res.status(400).json({ error: "Missing data" })
  }
  const conn = await db.getConnection()
  try {
    await conn.query(`USE ${currentDatabase}`)
    const [result] = await conn.query(
      "UPDATE feedback_log SET feedback = ? WHERE id_mongo = ?",
      [feedback, id_mongo]
    )
    res.json({ result: "Feedback updated" })
  } catch (err) {
    res.status(500).json({ error: err.message })
  } finally {
    conn.release()
  }
})

const PORT = process.env.PORT || 3350
app.listen(PORT, "0.0.0.0", () => console.log(`Server running on port ${PORT}`))