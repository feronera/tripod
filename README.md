# Pod starter kit: SuperBiz × SuperDev

ชุดตั้งต้นสำหรับ delivery pod ที่มีมนุษย์เพียงสองคนทำงานร่วมกับ agent
ใช้ใน workshop ภาคปฏิบัติ 2 วัน เรื่อง Agentic Development Lifecycle (ADLC)

- **SuperBiz** รับบทบาท PO, PM, BA และ Designer รับผิดชอบว่า "ทำอะไรและเพราะอะไร"
- **SuperDev** รับบทบาท SA, Dev, QA, Deploy และ MA (ดูแลระบบ) รับผิดชอบว่า "ทำอย่างไรและปลอดภัยหรือไม่"

agent ร่างงานของทุกบทบาท มนุษย์ตัดสินใจที่ gate 4 จุด
หลัก "ผู้เขียนและผู้อนุมัติเป็นคนละคน" รักษาไว้ด้วย cross-gate

| Gate | Artifact | Owner อนุมัติ | อีกคนตรวจทาน (cross) |
|---|---|---|---|
| 1 | intent.md | SuperBiz | SuperDev (ทำได้จริงและวัดผลได้หรือไม่) |
| 2 | spec.md (+ ux-brief.md) | SuperBiz | SuperDev |
| 3 | plan.md | SuperDev | SuperBiz (ยังตรงกับ intent หรือไม่) |
| 4 | PR / acceptance.md | SuperDev (โค้ด) | SuperBiz (ยอมรับตาม Success measure) |

กฎเพิ่มเติม
- **Risk tier:** ระบุใน intent.md (`Risk: low | medium | high`) งาน `high` ต้องมี escalation ลงชื่อเพิ่มที่ gate 2 และ 4 ดู `docs/risk-tiers.md`
- **WIP limit:** change ที่ผ่าน gate 1 แต่ยังไม่ผ่าน gate 4 เปิดพร้อมกันได้ไม่เกิน `wip_limit` ใน `pod.yml` (ค่าเริ่มต้น 2)
- **Stale approval:** การอนุมัติแต่ละครั้งเก็บ blob hash ของ artifact หาก artifact ถูกแก้หลังอนุมัติ gate-check จะไม่ผ่าน

## เริ่มต้นใช้งาน

โฟลเดอร์นี้เป็น template ให้คัดลอกไปเป็น repo ใหม่ของ pod

```bash
cp -R pod ~/my-pod && cd ~/my-pod && git init
# แก้ pod.yml: ใส่ชื่อและอีเมลจริงของ SuperBiz, SuperDev และ escalation
# อีเมลต้องตรงกับ git config user.email ของแต่ละคน
make setup
make check
git add -A && git commit -m "chore: start pod"
```

ต้องมี: Python 3.10 ขึ้นไป, git และ Claude Code ไม่ต้องติดตั้ง package เพิ่ม

## ลำดับงานของหนึ่ง change

1. SuperBiz: `scripts/new-change.sh order-history` แล้วใช้ skill `/superbiz:intent` ร่าง intent.md
2. Gate 1: SuperBiz `scripts/gate.sh docs/changes/001-order-history 1` แล้ว SuperDev ตรวจทานและรันคำสั่งเดียวกัน
3. SuperBiz: `/superbiz:ux-brief` และ `/superbiz:spec` แล้วผ่าน gate 2
4. SuperDev: `/superdev:plan` แล้วผ่าน gate 3
5. SuperDev: `/superdev:test-first` และ `/superdev:review` แล้วเปิด PR
6. SuperBiz: `/superbiz:acceptance` แล้วผ่าน gate 4 (SuperDev ลงชื่อก่อนในฐานะ owner)
7. SuperDev: `/superdev:release` และ SuperBiz: `/superbiz:release-notes`

## คำสั่ง

| คำสั่ง | ใช้ทำอะไร |
|---|---|
| `make setup` | ตรวจเครื่องมือ และเตรียมโฟลเดอร์ `.pod/` |
| `make test` | รัน unit test ทั้งหมด (`app/` และ scripts) |
| `make check` | `make test` และ `scripts/gate-check.sh --all` (CI รันคำสั่งนี้ทุก pull request) |
| `scripts/new-change.sh <slug>` | สร้าง `docs/changes/NNN-slug/intent.md` ปฏิเสธเมื่อถึง WIP limit |
| `scripts/gate.sh <change-dir> <1-4>` | ลงชื่อ gate ด้วยอีเมลจาก `git config user.email` บันทึกลง `gates.log` |
| `scripts/gate-check.sh <change-dir> [upto]` | ตรวจ gate ของ change เดียว |
| `scripts/gate-check.sh --all` | ตรวจทุก change (change ที่ยังไม่มี gates.log ถือเป็น draft) |
| `scripts/metrics.sh <change-dir>` หรือ `make metrics CHANGE=<change-dir>` | เวลาจาก commit แรกของ intent.md ถึงแต่ละ gate และ lead time |
| `touch .pod/lock-tests` | ล็อก tests ไม่ให้ agent แก้ |
| `touch .pod/kill-switch` | หยุด agent ทุกตัวที่โหลด plugin superdev |

## โหลด plugin

plugin อยู่ใน repo นี้ ใช้ `--plugin-dir` โหลดเฉพาะ session โดยไม่เปลี่ยนการตั้งค่าของเครื่อง

```bash
# เครื่องของ SuperBiz
claude --plugin-dir ./plugins/superbiz

# เครื่องของ SuperDev
claude --plugin-dir ./plugins/superdev
```

หากต้องการติดตั้งแบบถาวร repo นี้เป็น marketplace ชื่อ `adlc-pod` ได้ด้วย
(`/plugin marketplace add ./` แล้ว `/plugin install superbiz@adlc-pod` หรือ `superdev@adlc-pod`)

| Plugin | Skills | Agents | Hooks |
|---|---|---|---|
| superbiz | intent, ux-brief, spec, acceptance, release-notes | ba-researcher, ux-critic | biz-scope: แก้ได้เฉพาะ `docs/` |
| superdev | plan, test-first, review, release, incident | reviewer, monitor | kill-switch, protect-tests, gate-guard |

## โครงสร้าง

```
AGENTS.md, CLAUDE.md     กฎสำหรับ agent
pod.yml                  สมาชิก pod, escalation และ WIP limit
Makefile                 setup, test, check, metrics
app/orders.py            โดเมนตัวอย่าง: สถานะคำสั่งซื้อของลูกค้า
tests/                   unit test ของ app และ scripts
docs/gates.md            gate และคำถามตรวจ
docs/risk-tiers.md       ระดับความเสี่ยง
docs/pod-charter.md      ข้อตกลงของ pod
docs/parallel-agents.md  ให้ agent หลายตัวทำงานพร้อมกัน
docs/templates/          intent, ux-brief, spec, plan, acceptance
docs/changes/            change ของ pod (NNN-slug/)
scripts/                 new-change, gate, gate-check, metrics (lib.py เป็นตัวหลัก)
plugins/                 superbiz และ superdev
logs/sample-app.log      log สังเคราะห์สำหรับ lab incident
.github/workflows/       CI รัน make check
```

## ข้อควรรู้

- agent ไม่ลงชื่อ gate แทนมนุษย์ คำสั่ง `scripts/gate.sh` ต้องรันโดยมนุษย์เท่านั้น
- ข้อมูลใน `app/` และ `logs/` เป็นข้อมูลสังเคราะห์ทั้งหมด
- โฟลเดอร์ `.pod/` ไม่ถูก commit (อยู่ใน `.gitignore`) เพราะเป็นสถานะของเครื่องแต่ละเครื่อง
