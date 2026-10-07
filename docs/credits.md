# Credits

## pstack

แนวคิดด้านวิธีทำงานทางวิศวกรรมหลายข้อในชุดนี้ดัดแปลงมาจาก pstack ของ Lauren Tan
(https://github.com/cursor/plugins/tree/main/pstack) ซึ่งเผยแพร่ภายใต้ MIT License
Copyright (c) 2026 Lauren Tan

ชุดนี้ไม่ได้คัดลอกข้อความของ pstack แต่นำแนวคิดมาเขียนใหม่ให้เข้ากับ pod สองคนและ gate ของ pod
และเปลี่ยนแนวคิดที่สำคัญให้เป็นการตรวจด้วย script, hook หรือ CI

| แนวคิดจาก pstack | ใช้ใน pod อย่างไร |
|---|---|
| Foundational thinking, model the domain (โครงข้อมูลก่อน logic) | หัวข้อ `## Data shape` ใน plan.md ตรวจโดย gate 3 |
| Throughput checkpoint ของ poteto-mode | หัวข้อ `## Throughput checkpoint` ใน plan.md ตรวจโดย gate 3 |
| Separate before serializing shared state | `## Parallel parts` ที่ไฟล์ต้องไม่ทับกัน ตรวจโดย gate 3 |
| Sequence work into verifiable units | skill `/superdev:build`: หนึ่ง unit หนึ่ง commit ที่ test ผ่าน |
| Test behavior, not implementation (test ที่ยังผ่านเมื่อทุกฟังก์ชันคืนค่าว่าง) | `scripts/test-strength.sh` ใน `make check` และ 5 รูปแบบของ test อ่อนใน `/superdev:test-first` |
| Fix root causes | skill `/superdev:bug-fix` |
| ความเห็นจาก model อื่น (cross-model review) | agent `reviewer-second` และ `second_opinion` ใน review.md |
| Arena (หลายแนวทางพร้อมกันแล้วเลือก) | skill `/superdev:arena` ที่ใช้ test ที่ล็อกเป็นกรรมการ |
| Encode lessons in structure | กฎใน `docs/pod-charter.md`: กฎที่ถูกฝ่าซ้ำ 2 ครั้งต้องเป็น hook, script หรือ CI check |

ส่วน governance (gate, cross-approval, risk tier, WIP limit, audit log ใน gates.log และ merge ตาม risk)
เป็นของชุดนี้เอง
