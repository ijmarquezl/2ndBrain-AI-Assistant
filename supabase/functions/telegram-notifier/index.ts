import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.3'

const SUPABASE_URL = Deno.env.get('SUPABASE_URL') || ''
const SUPABASE_SERVICE_ROLE_KEY = Deno.env.get('SERVICE_ROLE_KEY') || ''
const TELEGRAM_TOKEN = Deno.env.get('TELEGRAM_BOT_TOKEN') || ''
const CHAT_ID = Deno.env.get('TELEGRAM_CHAT_ID') || ''
const USER_TIMEZONE = Deno.env.get('USER_TIMEZONE') || 'America/Mexico_City'

const supabase = createClient(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

async function sendTelegramMessage(text: string) {
    const url = `https://api.telegram.org/bot${TELEGRAM_TOKEN}/sendMessage`
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            chat_id: CHAT_ID,
            text: text,
            parse_mode: 'Markdown',
        }),
    })

    if (!response.ok) {
        console.error(`Telegram Error: ${await response.text()}`)
    } else {
        console.log(`Message sent: ${text}`)
    }
}

function getZonedTime(timeZone: string) {
    // Hack to get offset datetimes in pure Deno easily
    const now = new Date()
    const str = now.toLocaleString("en-CA", { timeZone, hour12: false }) // YYYY-MM-DD, HH:mm:ss
    // e.g., "2026-02-24, 23:18:22"
    const [datePart, timePart] = str.split(', ')
    const [y, m, d] = datePart.split('-').map(Number)
    const [h, min, s] = timePart.split(':').map(Number)

    return { datePart, timePart, nowTime: now.getTime(), y, m, d, h, min, s }
}

serve(async (req) => {
    console.log("🚀 Notifier Edge Function starting...")

    const zoned = getZonedTime(USER_TIMEZONE)
    const todayStr = zoned.datePart
    const currentWeekday = new Date().getDay() // 0 = Sun, 1 = Mon ... Deno uses Date.getDay()
    // Note: Python weekday() is Mon=0, Sun=6. Deno getDay() is Sun=0, Mon=1...
    // Wait, if python dias_semana is [0, 6] meaning Mon and Sun, in Deno that's 1 and 0.
    // We need to map Deno getDay() to Python weekday() to match db:
    // Deno: Sun=0, Mon=1, Tue=2, Wed=3, Thu=4, Fri=5, Sat=6
    // Python: Mon=0, Tue=1, Wed=2, Thu=3, Fri=4, Sat=5, Sun=6
    const pyWeekday = currentWeekday === 0 ? 6 : currentWeekday - 1

    console.log(`🕒 Time Check: ${todayStr} ${zoned.timePart} (TZ: ${USER_TIMEZONE}, Day: ${pyWeekday})`)

    try {
        const { data: tasks, error } = await supabase
            .from('tareas')
            .select('*')
            .in('estado', ['pendiente', 'aprobado'])

        if (error) throw error
        if (!tasks) return new Response('No tasks', { status: 200 })

        for (const task of tasks) {
            const tid = task.id
            const contenido = task.contenido
            const hora_limite_str = task.hora_limite // "16:00:00"
            const ultimo_rec = task.ultimo_recordatorio // ISO string
            const es_habito = task.es_habito
            const fecha_limite = task.fecha_limite // "YYYY-MM-DD" setup
            const dias_semana = task.dias_semana || []
            const fecha_fin_habito = task.fecha_fin_habito

            if (!hora_limite_str) continue

            // Check if notified today
            let already_notified_today = false
            if (ultimo_rec) {
                if (ultimo_rec.includes(todayStr)) {
                    already_notified_today = true
                } else {
                    // Check timezone conversion roughly
                    const dt = new Date(ultimo_rec)
                    const recStr = dt.toLocaleString("en-CA", { timeZone: USER_TIMEZONE, hour12: false })
                    if (recStr.includes(todayStr)) {
                        already_notified_today = true
                    }
                }
            }

            if (already_notified_today) continue

            let should_notify = false

            // Scenario A: Habit
            if (es_habito) {
                if (fecha_fin_habito && todayStr > fecha_fin_habito) {
                    should_notify = false // Expired
                } else if (dias_semana.length > 0) {
                    should_notify = dias_semana.includes(pyWeekday)
                } else {
                    should_notify = true // Daily
                }
            }
            // Scenario B: Deadline
            else if (fecha_limite) {
                const deadline_str = fecha_limite.split("T")[0]
                should_notify = (deadline_str === todayStr)
            }

            if (should_notify) {
                // Create deadline datetime for today
                const [hh, mm, ss] = hora_limite_str.split(':').map(Number)

                const nowMinutes = (zoned.h * 60) + zoned.min
                const deadlineMinutes = (hh * 60) + mm
                const diffMinutes = nowMinutes - deadlineMinutes

                const VALIDITY_WINDOW_MINUTES = 5

                if (diffMinutes >= 0 && diffMinutes <= VALIDITY_WINDOW_MINUTES) {
                    const msg = `⏰ **Recordatorio 2ndBrain**\n\nEs hora de: **${contenido}**\n(${hora_limite_str})`
                    await sendTelegramMessage(msg)

                    await supabase
                        .from('tareas')
                        .update({ ultimo_recordatorio: new Date().toISOString() })
                        .eq('id', tid)
                } else if (diffMinutes > VALIDITY_WINDOW_MINUTES) {
                    console.log(`Task ${tid} stale (Diff mins: ${diffMinutes}). Marking skipped.`)
                    await supabase
                        .from('tareas')
                        .update({ ultimo_recordatorio: new Date().toISOString() })
                        .eq('id', tid)
                }
            }
        }

        return new Response(JSON.stringify({ success: true }), { headers: { 'Content-Type': 'application/json' } })

    } catch (err) {
        console.error(err)
        return new Response(JSON.stringify({ error: String(err) }), { status: 500 })
    }
})
