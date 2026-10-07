# Gates

pod มีมนุษย์สองคน agent ช่วยร่างงานของทุกบทบาท แต่การตัดสินใจทำโดยมนุษย์ที่ gate 4 จุด
หลัก "ผู้เขียนและผู้อนุมัติเป็นคนละคน" รักษาไว้ด้วย cross-gate: ทุก gate ต้องมี owner อนุมัติ และอีกคนหนึ่งตรวจทาน

| Gate | Artifact | Owner อนุมัติ | อีกคนตรวจทาน (cross) | Risk: high |
|---|---|---|---|---|
| 1 | intent.md | SuperBiz | SuperDev (ทำได้จริงและวัดผลได้หรือไม่) | - |
| 2 | spec.md (+ ux-brief.md) | SuperBiz | SuperDev | + escalation |
| 3 | plan.md | SuperDev | SuperBiz (ยังตรงกับ intent หรือไม่) | - |
| 4 | PR / acceptance.md | SuperDev (โค้ด) | SuperBiz (ยอมรับตาม Success measure) | + escalation |

## Gate 4 มีสองการตรวจ

| การตรวจ | คำสั่ง | low | medium | high |
|---|---|---|---|---|
| merge-ready (merge เข้า main ได้) | `scripts/gate-check.sh <dir> 4` | owner + cross หรือบันทึก `role=auto` | owner | owner + cross + escalation |
| release-ready (ปล่อยขึ้น production ได้) | `scripts/release-check.sh <dir>` | owner + cross | owner + cross | owner + cross + escalation |

- release-ready ต้องไม่ stale และไม่มีบันทึก `event=revert`
- รายละเอียดและเงื่อนไขของ auto-merge อยู่ใน `docs/merge-by-risk.md`

## วิธีลงชื่อ

```bash
scripts/gate.sh docs/changes/001-slug 1     # owner ลงชื่อก่อน แล้ว cross ลงชื่อตาม
scripts/gate-check.sh docs/changes/001-slug  # ตรวจทุก gate ที่มีใน gates.log
```

- ตัวตนมาจาก `git config user.email` และบทบาทมาจาก `pod.yml`
- ลำดับ: owner ก่อน แล้ว cross แล้ว escalation (ถ้าต้องมี)
  ยกเว้น gate 4 หลังบันทึก `role=auto`: SuperBiz ลงชื่อ cross ได้ก่อน (ตรวจรับหลัง merge)
- gate N ลงชื่อได้เมื่อ gate N-1 ครบแล้วเท่านั้น
- แต่ละบรรทัดใน `gates.log` เก็บ blob hash ของ artifact หาก artifact ถูกแก้หลังอนุมัติ การอนุมัติจะ "stale" และต้องลงชื่อใหม่
- agent ไม่ลงชื่อ gate แทนมนุษย์

## คำถามตรวจของแต่ละ gate

### Gate 1: intent.md
- ปัญหามีหลักฐานจริง และระบุผู้ใช้ชัดเจนหรือไม่
- Success measure เป็นตัวเลขที่วัดได้ และมีค่าปัจจุบันหรือไม่
- Risk ตอบ 4 คำถามใน `docs/risk-tiers.md` แล้วหรือไม่
- (SuperDev) ทำได้ในขนาดของ change เดียวหรือไม่ และวัดผลได้ด้วยข้อมูลที่มีอยู่หรือไม่

### Gate 2: spec.md และ ux-brief.md
- ทุก requirement (R1, R2, ...) ตรวจได้ด้วย test หรือ demo หรือไม่
- edge cases ครอบคลุมข้อมูลว่าง ข้อมูลผิด และสิทธิ์การเข้าถึงหรือไม่
- ux-brief มีครบ 4 states (empty, loading, error, success) และข้อความภาษาไทยหรือไม่
- Flagged concerns ได้รับคำตอบหรือถูกยอมรับเป็นความเสี่ยงแล้วหรือไม่
- (SuperDev) มีอะไรที่ทำไม่ได้หรือแพงเกินจำเป็นหรือไม่

### Gate 3: plan.md
- (ตรวจโดย script) มี `## Data shape` ที่กรอกแล้ว, `## Throughput checkpoint` ครบ 4 บรรทัด
  และ `## Parallel parts` ที่เป็น `none: <เหตุผล>` หรือมีอย่างน้อย 2 ส่วนที่ไฟล์ไม่ทับกัน
  `scripts/gate.sh` ปฏิเสธการลงชื่อ และ `scripts/gate-check.sh` ไม่ผ่าน หากขาดข้อใด
- ทุก requirement มีไฟล์ที่ต้องแก้และวิธีพิสูจน์ (Proof)
- ลำดับงานเริ่มจาก test ที่ fail ก่อน
- Rollback ทำได้จริงและระบุขั้นตอน
- (SuperBiz) อ่าน "สรุปให้ SuperBiz" แล้วยังตรงกับ intent หรือไม่

### Gate 4: PR และ acceptance.md
- (SuperDev) `make check` ผ่าน (รวม test-strength) review.md มี `blockers: 0` และ tests ไม่ถูกแก้หลังล็อก
- (SuperBiz) ผลจาก demo ตรงกับ Success measure และ acceptance.md ระบุ accept หรือ reject พร้อมเหตุผล
- (Risk: high) escalation ตรวจและลงชื่อแล้ว
