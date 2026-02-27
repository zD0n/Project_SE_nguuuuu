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
  multipleStatements: true
})

app.get("/health", async (req, res) => {
  try {
    res.status(200).json({ status: "Online" })
  } catch (err) {
    res.status(500).json({ status: "Error" })
  }
})

app.get("/current-db", async (req, res) => {
  res.json({ database: currentDatabase })
})

app.get("/tables", async (req, res) => {
  const conn = await db.getConnection()
  try {
    await conn.query(`USE ${currentDatabase}`)
    const [rows] = await conn.query("SHOW TABLES")

    const tables = rows.map(row => Object.values(row)[0])

    res.json({ tables })
  } catch (err) {
    res.status(500).json({ error: err.message })
  } finally {
    conn.release()
  }
})

app.post("/log", async (req, res) => {
  const { snake_found, confidence, image_url } = req.body
  
  if (!snake_found) {
    return res.status(400).json({ error: "snake_found is required" })
  }

  const conn = await db.getConnection()

  try {
    await conn.query(`USE ${currentDatabase}`)

    const [result] = await conn.query(
      "INSERT INTO log (snake_found, confidence, image_url, created_at) VALUES (?, ?, ?, NOW())",
      [snake_found, confidence || null, image_url || null]
    )

    res.json({
      result: "logged successfully",
      id: result.insertId
    })

  } catch (err) {
    res.status(500).json({ error: err.message })
  } finally {
    conn.release()
  }
})

app.get("/summary", async (req, res) => {
  const conn = await db.getConnection()
  try {
    await conn.query(`USE ${currentDatabase}`)
    const [rows] = await conn.query("SELECT * FROM log ORDER BY created_at DESC LIMIT 100")

    res.json({ logs: rows, count: rows.length })
  } catch (err) {
    res.status(500).json({ error: err.message })
  } finally {
    conn.release()
  }
})

const PORT = process.env.PORT || 3350
const HOST = process.env.HOST || "0.0.0.0"
app.listen(PORT, HOST, () => console.log(`Server running on ${HOST}:${PORT}`))