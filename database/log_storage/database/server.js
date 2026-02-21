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
  const { sql } = req.body
  if (!sql) return res.status(400).json({ error: "SQL is required" })

  const conn = await db.getConnection()

  try {
    await conn.query(`USE ${currentDatabase}`)

    const [result] = await conn.query(sql)

    res.json({
      result: "executed successfully",
      affectedRows: result.affectedRows || 0,
      insertId: result.insertId || null
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
    const [rows] = await conn.query("SELECT * FROM log;")

    const tables = rows.map(row => Object.values(row)[0])

    res.json({ tables })
  } catch (err) {
    res.status(500).json({ error: err.message })
  } finally {
    conn.release()
  }
})

app.post("/query", async (req, res) => {
  const { sql } = req.body
  if (!sql) return res.status(400).json({ error: "SQL is required" })

  const conn = await db.getConnection()

  try {
    await conn.query(`USE ${currentDatabase}`)

    const statements = sql
      .split(";")
      .map(s => s.trim())
      .filter(s => s.length > 0)

    let lastRows = null
    let message = ""

    for (const stmt of statements) {
      const [rows] = await conn.query(stmt)

      const useMatch = stmt.match(/^USE\s+([a-zA-Z0-9_]+)/i)
      if (useMatch) {
        currentDatabase = useMatch[1]
      }

      if (Array.isArray(rows)) {
        lastRows = rows
        message = `${rows.length} row(s) returned`
      } else {
        message = "executed successfully"
      }
    }

    res.json({
      result: message,
      rows: lastRows
    })

  } catch (err) {
    res.status(500).json({ error: err.message })
  } finally {
    conn.release()
  }
})

const PORT = process.env.PORT || 3350
app.listen(PORT, () => console.log(`Server running on port ${PORT}`))